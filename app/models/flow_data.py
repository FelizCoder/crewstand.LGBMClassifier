from typing import List, Optional, Tuple
from pydantic import BaseModel


class FlowDataSummary(BaseModel):
    """
    Summary of processed flow data obtained from InfluxDB.

    Attributes:
    -----------
    Volume : float
        The total volume of fluid over the sampling period.
    Mean : float
        The average flow rate during the sampling period.
    Peak : float
        The maximum flow rate encountered during the sampling period.

    Class Methods:
    -------------
    from_influx_values(influx_values: List[Tuple[str, float]])
        Converts a list of (key, value) tuples from InfluxDB into a FlowDataSummary object.

    Parameters:
    -----------
    influx_values : List[Tuple[str, float]]
        A list of key-value tuples where keys represent the characteristic names ('Volume', 'Mean', 'Peak')
        and values are the corresponding numerical measurements.

    Returns:
    --------
    FlowDataSummary
        A new instance of FlowDataSummary with attributes populated from influx_values.

    Raises:
    -------
    ValueError
        If influx_values does not contain exactly one entry for 'Volume', 'Mean', and 'Peak' or if
        unexpected keys are present.

    Examples:
    ---------
    >>> influx_values = [('Volume', 123.45), ('Mean', 34.56), ('Peak', 78.90)]
    >>> fds = FlowDataSummary.from_influx_values(influx_values)
    >>> print(fds)
    FlowDataSummary(Volume=123.45, Mean=34.56, Peak=78.9)
    """

    Volume: float
    Mean: float
    Peak: float

    @classmethod
    def from_influx_values(cls, influx_values: List[Tuple[str, float]]):
        """
        Constructs a FlowDataSummary object from a list of (key, value) tuples extracted from InfluxDB.
        """

        characteristics = {value[0]: value[1] for value in influx_values}
        return cls(**characteristics)


class FlowClassifierFeatures(FlowDataSummary):
    Duration: float
    Hour: float
