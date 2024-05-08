import enum

class JobContainer(enum.Enum):

    BLACKSCHOLES="anakli/cca:parsec_blackscholes"
    CANNEAL="anakli/cca:parsec_canneal"
    DEDUP="anakli/cca:parsec_dedup"
    FERRET="anakli/cca:parsec_ferret"
    FREQMINE="anakli/cca:parsec_freqmine"
    RADIX="anakli/cca:splash2x_radix"
    VIPS="anakli/cca:parsec_vips"


class ContainerState(enum.Enum):

    UNKNOWN="unknown"
    CREATED="created"
    RUNNING="running"
    PAUSED="paused"
    EXITED="exited"

    @classmethod
    def fromStr(cls, status):
        value_to_key = {e.value: e.name for e in cls}
        key = value_to_key.get(status)
        if key:
            return cls[key]
        return cls.UNKNOWN
    
    @classmethod
    def isInProgress(cls, status):
        return status in [ContainerState.CREATED, ContainerState.RUNNING]
