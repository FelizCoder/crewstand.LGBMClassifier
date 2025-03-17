import threading
from typing import Optional
import json
from lightgbm import LGBMClassifier
import websocket
import pandas as pd

from app.models.flow_data import FlowClassifierFeatures, FlowDataSummary
from app.models.missions import CompletedFlowControlMission, EndUseType
from app.utils.config import config
from app.utils.influx_client import InfluxConnector
from app.utils.logger import logger


class WebSocketService:

    def __init__(self, influx: InfluxConnector, classifier: LGBMClassifier):
        self.mission_ws: Optional[websocket.WebSocketApp] = None
        self.influx = influx
        self.classifier = classifier

    def start(self):
        """Start WebSocket connections in daemon threads"""
        self._establish_connections()

    def _establish_connections(self):
        """Create and start WebSocket connection threads"""
        mission_thread = threading.Thread(target=self._run_mission_ws)
        mission_thread.daemon = True
        mission_thread.start()

    def _run_mission_ws(self):
        """Run mission WebSocket connection"""
        while True:
            try:
                self.mission_ws = websocket.WebSocketApp(
                    f"ws://{config.BACKEND_BASE}/v1/missions/flow/completed",
                    on_message=self._on_mission_message,
                    on_error=self._on_mission_error,
                    on_close=self._on_mission_close,
                    on_open=self._on_mission_open,
                )
                self.mission_ws.run_forever()
            except Exception as e:
                logger.error(f"mission WS error: {e}")
                threading.Event().wait(5)  # Wait before reconnecting

    def get_flow_summary(self, mission):
        # Fetching the flow summary from Influx DB
        return self.influx.get_flow_summary(mission.start_ts, mission.end_ts)

    def prepare_flow_features(
        self, flow_summary: FlowDataSummary, mission: CompletedFlowControlMission
    ):
        # Preparing flow features dictionary from the summarized data and mission
        scaling_factor = mission.flow_control_mission.duration_scaling_factor

        simulation_duration = (mission.end_ts - mission.start_ts).total_seconds()

        duration = scaling_factor * simulation_duration
        volume = scaling_factor * flow_summary.Volume

        if mission.flow_control_mission.actual_start_time:
            start_time = mission.flow_control_mission.actual_start_time
        else:
            start_time = mission.start_ts

        hour = start_time.hour + start_time.minute / 60 + start_time.second / 3600

        flow_features = FlowClassifierFeatures(
            Mean=flow_summary.Mean,
            Peak=flow_summary.Peak,
            Volume=volume,
            Duration=duration,
            Hour=hour,
        )
        return flow_features

    def predict(self, flow_dict):
        # Converting the flow features dict to a DataFrame and running prediction
        classifier_features = pd.DataFrame(flow_dict, index=[0])
        sorted_columns = classifier_features[self.classifier.feature_name_]
        prediction = self.classifier.predict(sorted_columns)
        return prediction

    def handle_mission_classification(self, mission):
        # Main flow using the helper functions
        flow_summary = self.get_flow_summary(mission)
        flow_features = self.prepare_flow_features(flow_summary, mission)
        prediction = self.predict(flow_features.model_dump())
        # Do something with prediction, for example, return it, store it or send it via websocket
        return prediction, flow_features

    def _on_mission_message(self, _ws, message: str) -> None:
        """Handle mission messages"""
        try:
            mission = CompletedFlowControlMission(**json.loads(message))
            logger.debug("Parsed mission: %s", {mission.model_dump_json(indent=2)})
            prediction, flow_features = self.handle_mission_classification(mission)
            logger.debug(f"Predicted end use: {prediction}")
            end_use = EndUseType(prediction[0])
            self.influx.write_classified_end_use(end_use, mission, flow_features)

        except Exception as e:
            logger.error(f"Error processing mission message: {e}")

    # WebSocket event handlers
    def _on_mission_open(self, _ws):
        logger.info("mission WebSocket opened")

    def _on_mission_error(self, _ws, error):
        logger.error(f"mission WebSocket error: {error}")

    def _on_mission_close(self, _ws, code, msg):
        logger.info(f"mission WebSocket closed: {code} - {msg}")
