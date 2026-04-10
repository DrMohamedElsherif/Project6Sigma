
# evaluation_router.py
from fastapi import APIRouter
from api.utils.file_utils import generate_chart
from api.charts.evaluation.boxplot import Boxplot

router = APIRouter()

#################################################

# Boxplot endpoint
@router.post("/boxplot")
async def generate_boxplot(request: dict):
    return await generate_chart(request, Boxplot, "error_processing")

@router.post("/histogram")
async def generate_histogram(request: dict):
    from .histogram import Histogram
    return await generate_chart(request, Histogram, "error_processing")


# Histogram endpoints
# @router.post("/histogram1")
# async def generate_histogram1(request: dict):
#     from .histogram1 import Histogram1
#     return await generate_chart(request, Histogram1, "error_processing")


# @router.post("/histogram2")
# async def generate_histogram2(request: dict):
#     from .histogram2 import Histogram2
#     return await generate_chart(request, Histogram2, "error_processing")


# @router.post("/histogram3")
# async def generate_histogram3(request: dict):
#     from .histogram3 import Histogram3
#     return await generate_chart(request, Histogram3, "error_processing")


# @router.post("/histogram4")
# async def generate_histogram4(request: dict):
#     from .histogram4 import Histogram4
#     return await generate_chart(request, Histogram4, "error_processing")


# @router.post("/histogram5")
# async def generate_histogram5(request: dict):
#     from .histogram5 import Histogram5
#     return await generate_chart(request, Histogram5, "error_processing")


# Individual endpoints
@router.post("/individual1")
async def generate_individual1(request: dict):
    from .individual1 import Individual1
    return await generate_chart(request, Individual1, "error_processing")


@router.post("/individual2")
async def generate_individual2(request: dict):
    from .individual2 import Individual2
    return await generate_chart(request, Individual2, "error_processing")


@router.post("/individual3")
async def generate_individual3(request: dict):
    from .individual3 import Individual3
    return await generate_chart(request, Individual3, "error_processing")


@router.post("/individual4")
async def generate_individual4(request: dict):
    from .individual4 import Individual4
    return await generate_chart(request, Individual4, "error_processing")


@router.post("/individual5")
async def generate_individual5(request: dict):
    from .individual5 import Individual5
    return await generate_chart(request, Individual5, "error_processing")


@router.post("/individual6")
async def generate_individual6(request: dict):
    from .individual6 import Individual6
    return await generate_chart(request, Individual6, "error_processing")


# Interval endpoints
@router.post("/interval1")
async def generate_interval1(request: dict):
    from .interval1 import Interval1
    return await generate_chart(request, Interval1, "error_processing")


@router.post("/interval2")
async def generate_interval2(request: dict):
    from .interval2 import Interval2
    return await generate_chart(request, Interval2, "error_processing")


@router.post("/interval3")
async def generate_interval3(request: dict):
    from .interval3 import Interval3
    return await generate_chart(request, Interval3, "error_processing")


@router.post("/interval4")
async def generate_interval4(request: dict):
    from .interval4 import Interval4
    return await generate_chart(request, Interval4, "error_processing")


@router.post("/interval5")
async def generate_interval5(request: dict):
    from .interval5 import Interval5
    return await generate_chart(request, Interval5, "error_processing")


@router.post("/interval6")
async def generate_interval6(request: dict):
    from .interval6 import Interval6
    return await generate_chart(request, Interval6, "error_processing")


# Matrix plot endpoints
@router.post("/matrixplot1")
async def generate_matrixplot1(request: dict):
    from .matrixplot1 import Matrixplot1
    return await generate_chart(request, Matrixplot1, "error_processing")


@router.post("/matrixplot2")
async def generate_matrixplot2(request: dict):
    from .matrixplot2 import Matrixplot2
    return await generate_chart(request, Matrixplot2, "error_processing")


@router.post("/matrixplot3")
async def generate_matrixplot3(request: dict):
    from .matrixplot3 import Matrixplot3
    return await generate_chart(request, Matrixplot3, "error_processing")


@router.post("/matrixplot4")
async def generate_matrixplot4(request: dict):
    from .matrixplot4 import Matrixplot4
    return await generate_chart(request, Matrixplot4, "error_processing")


# Pie chart endpoints
@router.post("/piechart1")
async def generate_piechart1(request: dict):
    from .piechart1 import Piechart1
    return await generate_chart(request, Piechart1, "error_processing")


@router.post("/piechart2")
async def generate_piechart2(request: dict):
    from .piechart2 import Piechart2
    return await generate_chart(request, Piechart2, "error_processing")


# Probability plot endpoints
@router.post("/probabilityplot1")
async def generate_probabilityplot1(request: dict):
    from .probabilityplot1 import Probabilityplot1
    return await generate_chart(request, Probabilityplot1, "error_processing")


@router.post("/probabilityplot2")
async def generate_probabilityplot2(request: dict):
    from .probabilityplot2 import Probabilityplot2
    return await generate_chart(request, Probabilityplot2, "error_processing")


@router.post("/probabilityplot3")
async def generate_probabilityplot3(request: dict):
    from .probabilityplot3 import Probabilityplot3
    return await generate_chart(request, Probabilityplot3, "error_processing")


@router.post("/probabilityplot4")
async def generate_probabilityplot4(request: dict):
    from .probabilityplot4 import Probabilityplot4
    return await generate_chart(request, Probabilityplot4, "error_processing")


@router.post("/probabilityplot5")
async def generate_probabilityplot5(request: dict):
    from .probabilityplot5 import Probabilityplot5
    return await generate_chart(request, Probabilityplot5, "error_processing")


# Scatter plot endpoints
@router.post("/scatterplot1")
async def generate_scatterplot1(request: dict):
    from .scatterplot1 import Scatterplot1
    return await generate_chart(request, Scatterplot1, "error_processing")


@router.post("/scatterplot2")
async def generate_scatterplot2(request: dict):
    from .scatterplot2 import Scatterplot2
    return await generate_chart(request, Scatterplot2, "error_processing")


@router.post("/scatterplot3")
async def generate_scatterplot3(request: dict):
    from .scatterplot3 import Scatterplot3
    return await generate_chart(request, Scatterplot3, "error_processing")


@router.post("/scatterplot4")
async def generate_scatterplot4(request: dict):
    from .scatterplot4 import Scatterplot4
    return await generate_chart(request, Scatterplot4, "error_processing")


@router.post("/scatterplot5")
async def generate_scatterplot5(request: dict):
    from .scatterplot5 import Scatterplot5
    return await generate_chart(request, Scatterplot5, "error_processing")


# Time series plot endpoints
@router.post("/timeseriesplot1")
async def generate_timeseriesplot1(request: dict):
    from .timeseriesplot1 import Timeseriesplot1
    return await generate_chart(request, Timeseriesplot1, "error_processing")


@router.post("/timeseriesplot2")
async def generate_timeseriesplot2(request: dict):
    from .timeseriesplot2 import Timeseriesplot2
    return await generate_chart(request, Timeseriesplot2, "error_processing")


@router.post("/timeseriesplot3")
async def generate_timeseriesplot3(request: dict):
    from .timeseriesplot3 import Timeseriesplot3
    return await generate_chart(request, Timeseriesplot3, "error_processing")


@router.post("/timeseriesplot4")
async def generate_timeseriesplot4(request: dict):
    from .timeseriesplot4 import Timeseriesplot4
    return await generate_chart(request, Timeseriesplot4, "error_processing")


@router.post("/timeseriesplot5")
async def generate_timeseriesplot5(request: dict):
    from .timeseriesplot5 import Timeseriesplot5
    return await generate_chart(request, Timeseriesplot5, "error_processing")

@router.post("/multi-variant")
async def generate_multi_variant(request: dict):
    from .multi_vari_chart import MultiVariChart
    return await generate_chart(request, MultiVariChart, "error_processing", extension="pdf")



