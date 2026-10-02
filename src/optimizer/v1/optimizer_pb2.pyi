from ortools.sat import cp_model_pb2 as _cp_model_pb2
from ortools.sat import sat_parameters_pb2 as _sat_parameters_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SolveRequest(_message.Message):
    __slots__ = ("model", "parameters")
    MODEL_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    model: _cp_model_pb2.CpModelProto
    parameters: _sat_parameters_pb2.SatParameters
    def __init__(self, model: _Optional[_Union[_cp_model_pb2.CpModelProto, _Mapping]] = ..., parameters: _Optional[_Union[_sat_parameters_pb2.SatParameters, _Mapping]] = ...) -> None: ...

class SolveResponse(_message.Message):
    __slots__ = ("result",)
    RESULT_FIELD_NUMBER: _ClassVar[int]
    result: _cp_model_pb2.CpSolverResponse
    def __init__(self, result: _Optional[_Union[_cp_model_pb2.CpSolverResponse, _Mapping]] = ...) -> None: ...
