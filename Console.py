from SQLS.DB_Operations import setParcelMass, getZeroMassParcel
from APIs.pochtaApi import getMass
from pprint import pprint
from traceback import print_exc


def setParcelMasses():
    """Восстановить нулевые массы отправлений
    """

    parcel_list = getZeroMassParcel()

    for parcel in parcel_list:
        setParcelMass(parcel, getMass(parcel))


try:

    setParcelMasses()

except Exception as e:
    pprint(e) 
    print_exc()

