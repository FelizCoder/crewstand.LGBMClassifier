from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from app.models.flow_data import FlowClassifierFeatures, FlowDataSummary
from app.models.missions import CompletedFlowControlMission, EndUseType
from app.utils.config import config
from app.utils.logger import logger


class InfluxConnector:
    """
    Connector to interact with InfluxDB for writing and reading data.

    Attributes
    bucket : str
        The InfluxDB bucket where data will be written.
    client : InfluxDBClient
        The client instance used to interact with InfluxDB.
    write_api : WriteApi
        The API instance used to write data to InfluxDB.

    Methods
    __init__(
        url=config.INFLUXDB_URL.unicode_string(),
        token=config.INFLUXDB_TOKEN,
        org=config.INFLUXDB_ORG,
        bucket=config.INFLUXDB_BUCKET
    )
        Initializes the InfluxConnector with the specified InfluxDB connection parameters.
    write_pid(pid: PID, timestamp_ns: int)
        Writes PID controller data to InfluxDB.
    _write(point)
        Writes a data point to InfluxDB and handles exceptions.
    """

    def __init__(
        self,
        url=config.INFLUXDB_URL.unicode_string(),
        token=config.INFLUXDB_TOKEN,
        org=config.INFLUXDB_ORG,
        bucket=config.INFLUXDB_BUCKET,
    ):

        self.bucket = bucket
        self.client = InfluxDBClient(
            url=url,
            token=token,
            org=org,
            debug=(config.DEBUG_LEVEL == "DEBUG"),
            timeout=250,
        )

        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()

    def get_flow_summary(self, start_ts: datetime, end_ts: datetime):
        """
        Retrieves and calculates aggregated flow data characteristics
        from InfluxDB within a specified time range.

        Parameters
        ----------
        start_ts : datetime
            The start of the time range from which to retrieve flow data.
        end_ts : datetime
            The end of the time range from which to retrieve flow data.

        Returns
        -------
        FlowDataSummary
            An object containing the total volume, mean flow rate, and peak flow rate derived
            from the flowmeter data within the specified time range.

        Raises
        ------
        InfluxDBError
            If there is an issue with the query or the connection to the InfluxDB.

        ValueError
            If there are unexpected keys returned from the InfluxDB query.

        Notes
        -----
        This method executes an InfluxDB query to obtain readings for a flowmeter identified by id "0"
        and calculates various characteristics: total volume, mean flow rate, and peak flow rate.

        The query uses Flux language and is designed to work against an InfluxDB v2.x server. It may
        require modifications for different InfluxDB versions or measurement structures.

        Examples
        --------
        To get flow characteristics between '2022-01-01 00:00:00' and '2022-01-02 00:00:00':

        >>> start_ts = datetime(2022, 1, 1)
        >>> end_ts = datetime(2022, 1, 2)
        >>> flow_characteristics = influx_connector.get_flow_characteristics(start_ts, end_ts)
        >>> print(flow_characteristics)
        FlowDataSummary(Volume=12345.67, Mean=123.45, Peak=678.90)

        """

        query = f"""data = from(bucket: "{self.bucket}")
                        |> range(start: {start_ts.isoformat()}Z, stop: {end_ts.isoformat()}Z)  
                        |> filter(fn: (r) => r["_measurement"] == "flowmeter")
                        |> filter(fn: (r) => r["_field"] == "reading")
                        |> filter(fn: (r) => r["id"] == "0")
                    
                    flowMean = data
                        |> mean(column: "_value")
                        |> yield(name: "Mean")

                    flowMax = data
                        |> max(column: "_value")
                        |> yield(name: "Peak")

                    flowVolume = data
                        |> integral(unit: 1m, column: "_value")
                        |> yield(name: "Volume")"""

        flow_tables = self.query_api.query(query)
        flow_values = flow_tables.to_values(columns=["result", "_value"])
        flow_summary = FlowDataSummary.from_influx_values(flow_values)

        logger.debug("Flow summary: %s", flow_summary.model_dump_json(indent=2))

        return flow_summary

    def write_classified_end_use(
        self,
        end_use: EndUseType,
        mission: CompletedFlowControlMission,
        flow_features: FlowClassifierFeatures,
    ):
        point = (
            Point("Classification")
            .field("end_use", end_use.value)
            .time(mission.start_ts, WritePrecision.NS)
        )
        for key, value in flow_features.model_dump().items():
            point.tag(key, value)
        self._write(point)

    def _write(self, point):
        try:
            self.write_api.write(bucket=self.bucket, record=point)
        except Exception as e:
            logger.error(f"Failed to write to InfluxDB: {e}")
