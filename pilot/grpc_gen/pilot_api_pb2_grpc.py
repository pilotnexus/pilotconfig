# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2
from . import pilot_api_pb2 as pilot__api__pb2

class PilotApiStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetFwConfig = channel.unary_unary(
                '/pilot_api.PilotApi/GetFwConfig',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=pilot__api__pb2.FwConfigResponse.FromString,
                )
        self.GetID = channel.unary_unary(
                '/pilot_api.PilotApi/GetID',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=pilot__api__pb2.IdResponse.FromString,
                )
        self.SetName = channel.unary_unary(
                '/pilot_api.PilotApi/SetName',
                request_serializer=google_dot_protobuf_dot_wrappers__pb2.StringValue.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_wrappers__pb2.BoolValue.FromString,
                )
        self.SetDebugMode = channel.unary_unary(
                '/pilot_api.PilotApi/SetDebugMode',
                request_serializer=pilot__api__pb2.DebugModeMsg.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_wrappers__pb2.BoolValue.FromString,
                )
        self.GetDebugMode = channel.unary_unary(
                '/pilot_api.PilotApi/GetDebugMode',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=pilot__api__pb2.DebugModeMsg.FromString,
                )
        self.GetMetricInfo = channel.unary_stream(
                '/pilot_api.PilotApi/GetMetricInfo',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=pilot__api__pb2.MetricInfo.FromString,
                )
        self.GetFloatMetric = channel.unary_stream(
                '/pilot_api.PilotApi/GetFloatMetric',
                request_serializer=google_dot_protobuf_dot_wrappers__pb2.StringValue.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_wrappers__pb2.FloatValue.FromString,
                )
        self.GetMetric = channel.unary_stream(
                '/pilot_api.PilotApi/GetMetric',
                request_serializer=google_dot_protobuf_dot_wrappers__pb2.StringValue.SerializeToString,
                response_deserializer=pilot__api__pb2.MetricMsg.FromString,
                )
        self.SetFirmware = channel.unary_stream(
                '/pilot_api.PilotApi/SetFirmware',
                request_serializer=pilot__api__pb2.FirmwareRequest.SerializeToString,
                response_deserializer=pilot__api__pb2.FirmwareStatus.FromString,
                )


class PilotApiServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetFwConfig(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetID(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetName(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetDebugMode(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetDebugMode(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetMetricInfo(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetFloatMetric(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetMetric(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetFirmware(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_PilotApiServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetFwConfig': grpc.unary_unary_rpc_method_handler(
                    servicer.GetFwConfig,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=pilot__api__pb2.FwConfigResponse.SerializeToString,
            ),
            'GetID': grpc.unary_unary_rpc_method_handler(
                    servicer.GetID,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=pilot__api__pb2.IdResponse.SerializeToString,
            ),
            'SetName': grpc.unary_unary_rpc_method_handler(
                    servicer.SetName,
                    request_deserializer=google_dot_protobuf_dot_wrappers__pb2.StringValue.FromString,
                    response_serializer=google_dot_protobuf_dot_wrappers__pb2.BoolValue.SerializeToString,
            ),
            'SetDebugMode': grpc.unary_unary_rpc_method_handler(
                    servicer.SetDebugMode,
                    request_deserializer=pilot__api__pb2.DebugModeMsg.FromString,
                    response_serializer=google_dot_protobuf_dot_wrappers__pb2.BoolValue.SerializeToString,
            ),
            'GetDebugMode': grpc.unary_unary_rpc_method_handler(
                    servicer.GetDebugMode,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=pilot__api__pb2.DebugModeMsg.SerializeToString,
            ),
            'GetMetricInfo': grpc.unary_stream_rpc_method_handler(
                    servicer.GetMetricInfo,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=pilot__api__pb2.MetricInfo.SerializeToString,
            ),
            'GetFloatMetric': grpc.unary_stream_rpc_method_handler(
                    servicer.GetFloatMetric,
                    request_deserializer=google_dot_protobuf_dot_wrappers__pb2.StringValue.FromString,
                    response_serializer=google_dot_protobuf_dot_wrappers__pb2.FloatValue.SerializeToString,
            ),
            'GetMetric': grpc.unary_stream_rpc_method_handler(
                    servicer.GetMetric,
                    request_deserializer=google_dot_protobuf_dot_wrappers__pb2.StringValue.FromString,
                    response_serializer=pilot__api__pb2.MetricMsg.SerializeToString,
            ),
            'SetFirmware': grpc.unary_stream_rpc_method_handler(
                    servicer.SetFirmware,
                    request_deserializer=pilot__api__pb2.FirmwareRequest.FromString,
                    response_serializer=pilot__api__pb2.FirmwareStatus.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'pilot_api.PilotApi', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class PilotApi(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GetFwConfig(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/pilot_api.PilotApi/GetFwConfig',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            pilot__api__pb2.FwConfigResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetID(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/pilot_api.PilotApi/GetID',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            pilot__api__pb2.IdResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SetName(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/pilot_api.PilotApi/SetName',
            google_dot_protobuf_dot_wrappers__pb2.StringValue.SerializeToString,
            google_dot_protobuf_dot_wrappers__pb2.BoolValue.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SetDebugMode(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/pilot_api.PilotApi/SetDebugMode',
            pilot__api__pb2.DebugModeMsg.SerializeToString,
            google_dot_protobuf_dot_wrappers__pb2.BoolValue.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetDebugMode(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/pilot_api.PilotApi/GetDebugMode',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            pilot__api__pb2.DebugModeMsg.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetMetricInfo(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(request, target, '/pilot_api.PilotApi/GetMetricInfo',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            pilot__api__pb2.MetricInfo.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetFloatMetric(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(request, target, '/pilot_api.PilotApi/GetFloatMetric',
            google_dot_protobuf_dot_wrappers__pb2.StringValue.SerializeToString,
            google_dot_protobuf_dot_wrappers__pb2.FloatValue.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetMetric(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(request, target, '/pilot_api.PilotApi/GetMetric',
            google_dot_protobuf_dot_wrappers__pb2.StringValue.SerializeToString,
            pilot__api__pb2.MetricMsg.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SetFirmware(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(request, target, '/pilot_api.PilotApi/SetFirmware',
            pilot__api__pb2.FirmwareRequest.SerializeToString,
            pilot__api__pb2.FirmwareStatus.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)