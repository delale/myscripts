#!/~/CSCenv/bin python3
# run from /CSC_corpus #

# --------------------------------------- #
# Alessandro De Luca 17/05/2022           #
# --------------------------------------- #

# IMPORTS #
import numpy as np
import pandas as pd
import scipy
import scipy.spatial
import shapely.geometry


def ED(x: np.array, participant_arr: np.array, category_arr: np.array, global_ed=False) -> pd.DataFrame:
    """Calculates the Euclidean distance from the local centroid of the points.

    Calculates for each participant ID a local/global centroid and then calculates the
    Euclidean distance from the local centroid for all points in each category.
    Returns the ED of all points for (each category and) each participant.

    Args:
        x: Features array.
        participant_arr: The participant array (i.e. speaker ID).
        category_arr: The category array by which to calculate the ED.
            If None, the calculation by category is skipped.
        global_ed: If True the distance from the global centroid is calculated (default=False).

    Returns:
        A pd.DataFrame containing the information about Participant ID, (Category)
        and the Euclidean distance from the local or global center
    """

    participant = []
    category = []
    ed = []

    if global_ed:
        c = np.mean(x, axis=0)  # global centroid

    for ID in np.unique(participant_arr):
        # get the reference ids
        ref_id = np.where(participant_arr == ID)[0]

        if not global_ed:
            c = np.mean(x[ref_id], axis=0)  # local centroid

        if category_arr is not None:
            for CAT in np.unique(category_arr):

                ref = np.where(category_arr == CAT)[0]
                ref = ref[np.isin(ref, ref_id)]

                # calculate euclidean distance
                ed_tmp = np.sqrt(np.sum(np.square(x[ref]-c), axis=0))

                participant.append(np.array([ID]*len(ed_tmp)))
                category.append(np.array([CAT]*len(ed_tmp)))
                ed.append(ed_tmp)

        else:
            # calculate euclidean distance
            ed_tmp = np.sqrt(np.sum(np.square(x[ref_id]-c), axis=0))

            participant.append(np.array([ID]*len(ed_tmp)))
            ed.append(ed_tmp)

    # concatenate values
    participant = np.concatenate(participant)
    ed = np.concatenate(ed)

    # create df
    if len(category) > 0:
        category = np.concatenate(category)

        results = pd.DataFrame(
            {
                'ParticipantID': participant,
                'Category': category,
                'ED': ed
            }
        )

    else:
        results = pd.DataFrame(
            {
                'ParticipantID': participant,
                'ED': ed
            }
        )

    return results


def Var(x: np.array, participant_arr: np.array, category_arr: np.array) -> pd.DataFrame:
    """Calculates the variance of the coordinates locally.

    Calculates for each participant ID a local variances.

    Args:
        x: Features array.
        participant_arr: The participant array (i.e. speaker ID).
        category_arr: The category array by which to calculate the variance.
            If None, the calculation by category is skipped.

    Returns:
        A pd.DataFrame containing the information about Participant ID, (Category)
        and the variamce locally.
    """

    participant = []
    category = []
    var = []

    for ID in np.unique(participant_arr):
        # get the reference ids
        ref_id = np.where(participant_arr == ID)[0]

        if category_arr is not None:
            for CAT in np.unique(category_arr):

                ref = np.where(category_arr == CAT)[0]
                ref = ref[np.isin(ref, ref_id)]

                # calculate euclidean distance
                var_tmp = np.var(x[ref])

                participant.append(ID)
                category.append(CAT)
                var.append(var_tmp)

        else:
            # calculate euclidean distance
            var_tmp = np.var(x[ref_id])

            participant.append(ID)
            var.append(var_tmp)

    # create df
    if len(category) > 0:

        results = pd.DataFrame(
            {
                'ParticipantID': participant,
                'Category': category,
                'Var': var
            }
        )

    else:
        results = pd.DataFrame(
            {
                'ParticipantID': participant,
                'Var': var
            }
        )

    return results


def polygon_dims(x: np.array, y: np.array) -> tuple:
    """Calculates the polygon perimiter and area.

    Args:
        x: x coordinates.
        y: y coordinate.

    Returns: 
        Tuple containing the polygon perimeter and area.
    """
    polygon = shapely.geometry.Polygon(zip(x, y))

    return polygon.length, polygon.area


def f_test(x: np.array, y: np.array) -> set:
    """F-test for population variance.

    Args:
        x: 1st population data.
        y: 2nd population data.

    Returns:
        A set containing F statistic, DoF (DoFN, DoFD), p-value
    """

    f = np.var(x, ddof=1) / np.var(y, ddof=1)
    dofn = x.size - 1
    dofd = y.size - 1
    p = 1 - scipy.stats.f.cdf(f, dofn, dofd)

    return (f, (dofn, dofd), p)


def find_convex_hull(points: np.ndarray) -> set:
    """Finds the convex hull of the points.

    Args:
        points: points to find convex hull.

    Returns:
        Vertices, perimeter, and area of the convex hull.
    """

    hull = scipy.spatial.ConvexHull(points)

    return points[hull.vertices], hull.area, hull.volume


if __name__ == '__main__':
    X = np.random.randn(200, 2)

    y = np.repeat(np.arange(10), 20)
    cat = np.array([0, 1, 2, 3, 4]*40)

    # res = ED(x=X, participant_arr=y, category_arr=cat)
    # res = polygon_dims(x=X[:, 0], y=X[:, 1])
    res = Var(x=X, participant_arr=y, category_arr=cat)
    print(res)
