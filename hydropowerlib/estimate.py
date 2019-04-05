logger = logging.getLogger(__name__)

def missing_parameters(hpp, dV_hist=None, file_turb_graph)
    if not can_estimate(hpp, dV_hist):
        logger.error(f'The input data is not sufficient for plant {hpp.name}')
        raise RuntimeError(f'The input data is not sufficient for plant {hpp.name}')

    if hpp.dV_res is None:
        dV_res_from_dV_hist(hpp, hpp.dV_hist)
    if hpp.dV_n is None:
        dV_n_from_dV_hist(hpp, hpp.dV_hist)
    if hpp.P_n is None != hpp.h_n is None:
        P_n_or_h_n_from_characteristic_equation_at_nominal_load(hpp)
    if hpp.turb_type is None:
        turb_type_from_phase_diagram(hpp, file_turb_graph)

    logger.debug(f'''
        Plant {hpp.name}
        ----------------
        Nominal water flow  : {hpp.dV_n} m3/s
        Nominal head        : {hpp.h_n} m
        Nominal power       : {hpp.P_n} W
        Residual water flow : {hpp.dV_res} m3/s
        Turbine type        : {hpp.turb_type}
    ''')

def can_estimate(hpp, dV_hist=None):
    """
    Test if the input data is sufficient to simulate the plant

    The simulation is feasible if two parameters among `dV_n`, `h_n` and
    `P_n` are known. If dV_n is not known, it can be extrapolated from
    dV_hist.

    The logical expression verifying the feasibility is
    `(h_n and P_n) or ((h_n or P_n) and (dV_hist or dV_n))`

    """
    return (((hpp.h_n is not None) and (hpp.P_n is not None)) or
            (((hpp.h_n is not None) or (hpp.P_n is not None)) and
                ((dV_hist is not None) or (hpp.dV_n is not None))))

def dV_res_from_dV_hist(hpp, dV_hist):
    """
    Estimate value for residual flow volume dV_res

    dV_res is calculated from the mean flow duration curve over the historic flow volume `dV_hist`.
    If dV_hist is not given, dV_res is set to 0.

    Returns
    -------
    dV_res : float

    References
    ----------
    [1] Bundesamt für Konjunkturfragen. Wahl, Dimensionierung und Abnahme einer Kleinturbine, 1995.
    """
    if dV_hist is None:
        return 0

    # Select last 10 years
    dV_hist = dV_hist.loc[dV_hist.index[-1] - pd.tseries.offsets.DateOffset(years=10):]

    # Averaged yearly profile
    dV_mean = dV_hist.groupby(dV_hist.index.dayofyear).mean()

    # 0.05 quantile <-> 347 day in flow duration curve
    dV_347 = dV_mean.quantile(0.05)

    if dV_347 <= 0.06:
        hpp.dV_res = 0.05
    elif dV_347 <= 0.16:
        hpp.dV_res = 0.05 + (dV_347 - 0.06) * 8 / 10
    elif dV_347 <= 0.5:
        hpp.dV_res = 0.130 + (dV_347 - 0.16) * 4.4 / 10
    elif dV_347 <= 2.5:
        hpp.dV_res = 0.28 + (dV_347 - 0.5) * 31 / 100
    elif dV_347 <= 10:
        hpp.dV_res = 0.9 + (dV_347 - 2.5) * 21.3 / 100
    elif dV_347 <= 60:
        hpp.dV_res = 2.5 + (dV_347 - 10) * 150 / 1000
    else:
        hpp.dV_res = 10

def dV_n_from_dV_hist(hpp, dV_hist):
    """
    Estimate value for `dV_n`, the nominal water flow through the turbine

    If P_n and h_n are known, dV_n is calculated through equation
    P_n=h_n*dV_n*g*rho*eta_g_n*eta_t_n Where g=9.81 m/s², rho=1000 kg/m³,
    eta_g_n (nominal generator efficiency)=0.95 and eta_t_n (nominal
    turbine efficiency)=0.9 Otherwise dV_n is calculated from the flow
    duration curve over several years, after subtracting dV_res. It is the
    water flow reached or exceeded 20% of the time.

    Returns
    -------
    dV_n : float
    """
    if hpp.h_n is not None and hpp.P_n is not None:
        hpp.dV_n = hpp.P_n/(hpp.h_n*9.81*1000*0.9*0.95)
    else:
        fdc = pd.Series(hpp.dV_hist.sort_values(by='dV', ascending=False).dV.values - hpp.dV_res,
                        index=np.linspace(0, 100, num= hpp.dV_hist.count()))
        hpp.dV_n = np.interp(20, fdc.index, fdc.values)

def P_n_or_h_n_from_characteristic_equation_at_nominal_load(hpp):
    """
    Estimate value for `P_n` or `h_n` from characteristic equation

    P_n = h_n*dV_n*g*rho*eta_g_n*eta_t_n

    Where g=9.81 m/s², rho=1000 kg/m³,
          eta_g_n=0.95 (nominal generator efficiency) and
          eta_t_n (nominal turbine efficiency)=0.9
    """
    assert (hpp.h_n is not None or hpp.P_n is not None) and hpp.dV_n is None, "h_n and dV_n must be known for estimating P_n"

    eta_g_n = 0.95  # Assumed as 0.95
    eta_t_n = 0.9   # At full load the same for all turbine types

    if hpp.h_n is None:
        hpp.h_n = hpp.P_n/(hpp.dV_n * 9.81 * 1000 * eta_g_n * eta_t_n)
    elif hpp.P_n is None:
        hpp.P_n = hpp.h_n * hpp.dV_n * 9.81 * 1000 * eta_g_n * eta_t_n

def eta_g_n_from_P_n(hpp):
    r"""
    Calculate the nominal efficiency of the generator based on the nominal power of the plant

    References
    ----------
    [1] Bundesamt für Konjunkturfragen. Wahl, Dimensionierung und Abnahme einer Kleinturbine, 1995.
    """
    if P_n < 1000:
        eta_g_n = 80
    elif P_n < 5000:
        eta_g_n = 80 + (P_n - 1000) / 1000 * 5 / 4
    elif P_n < 20000:
        eta_g_n = 85 + (P_n - 5000) / 1000 * 5 / 15
    elif P_n < 100000:
        eta_g_n = 90 + (P_n - 20000) / 1000 * 5 / 80
    else:
        eta_g_n = 95

    hpp.eta_g_n = eta_g_n / 100

def turb_type_from_phase_diagram(hpp, file_turb_graph):
    """
    Estimate turbine type based h_n/dV_n characteristic diagram

    Fetches type of the requested hydropower turbine by situating it on a
    h_n/dV_n characteristic diagram of different turbines. The
    characteristic zones of each turbine are polygons in a dV_n / h_n plan
    and are defined by their angles.

    The list of angles for each type of turbine is given in
    "data/charac_diagrams.csv" and is based on
    https://de.wikipedia.org/wiki/Wasserturbine#/media/File:Kennfeld.PNG
    :return:
    hpp : Modelchain
    """

    def ccw(A, B, C):
        """
        Function to check if three points are called counterclockwise or clockwise
        Based on http://bryceboe.com/2006/10/23/line-segment-intersection-algorithm/
        :param A: [float, float]
        Coordinates of the first point
        :param B: [float, float]
        Coordinates of the second point
        :param C: [float, float]
        Coordinates of the third point
        :return:
        True if A, B and C are in counterclockwise order
        False if A, B and C are in clockwise order
        """
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])


    def intersec(A, B, C):
        """
        Function to determine if the half line defined as y=yA and x>=xA crosses the [BC[ segment
        Based on http://bryceboe.com/2006/10/23/line-segment-intersection-algorithm/
        :param A: [float, float]
        :param B: [float, float]
        :param C: [float, float]
        :return: bool
        """
        if B == C:
            # if [BC] is a point
            return False
        else:
            if B[1] == C[1]:
                # if [BC[ is horizontal
                # the segment and the horizontal half-line are parallel and never cross
                # (overlapping is not considered an intersection here)
                return False
            elif A[1] == B[1] and A[0] <= B[0]:
                # in order not to count twice an intersection on an angle of the polygon,
                # only the segment [BC[ is considered
                return True
            elif A[1] == C[1]:
                return False
            else:
                # define a point on the horizontal half-line starting in A
                # check if the two segments intersect
                D = (max(B[0], C[0]) + 1, A[1])
                return ccw(A, C, B) != ccw(D, C, B) and ccw(A, D, C) != ccw(A, D, B)

    try:
        df = pd.read_csv(os.path.join(os.path.join(os.path.dirname(__file__), 'data'), file_turb_graph),index_col=0)
    except IOError:
        logger.info(f'No file {file_turb_graph} in data folder')
        raise
    turbine_types = []
    charac_diagrams = pd.DataFrame()

    for col in df.columns:
        turbine_type = col.split('_')[0]
        if turbine_type not in turbine_types:
            turbine_types.append(turbine_type)
            charac_diagrams[turbine_type] = ""
        for i in df.index:
            if col.split('_')[1] == 'dV':
                charac_diagrams.at[i, turbine_type] = df.loc[i, col]
            elif col.split('_')[1] == 'h':
                charac_diagrams.at[i, turbine_type] = [charac_diagrams.loc[i, turbine_type], df.loc[i, col]]

    for turbine_type in turbine_types:
        intersections = 0
        for i in charac_diagrams.index:
            if i == len(charac_diagrams.index):
                if intersec([hpp.dV_n/hpp.turb_num,hpp.h_n], charac_diagrams.loc[i, turbine_type], charac_diagrams.loc[1, turbine_type]):
                    intersections = intersections + 1
            else:
                if (charac_diagrams.loc[i + 1, turbine_type])[0] != (charac_diagrams.loc[i + 1, turbine_type])[0] or (charac_diagrams.loc[i + 1, turbine_type])[1] != (charac_diagrams.loc[i + 1, turbine_type])[1]:
                    if intersec([hpp.dV_n/hpp.turb_num,hpp.h_n], charac_diagrams.loc[i, turbine_type], charac_diagrams.loc[1, turbine_type]):
                        intersections = intersections + 1
                    break
                else:
                    if intersec([hpp.dV_n/hpp.turb_num,hpp.h_n], charac_diagrams.loc[i, turbine_type], charac_diagrams.loc[i + 1, turbine_type]):
                        intersections = intersections + 1
        if intersections % 2 != 0:
            hpp.turb_type = turbine_type
            break
    else:
        hpp.turb_type = 'dummy'
        logger.warning(f'Turbine type could not be defined for plant {hpp.name}. Dummy type used')
