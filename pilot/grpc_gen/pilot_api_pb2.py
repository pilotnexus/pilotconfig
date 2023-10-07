# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: pilot_api.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0fpilot_api.proto\x12\tpilot_api\x1a\x1bgoogle/protobuf/empty.proto\x1a\x1egoogle/protobuf/wrappers.proto\"2\n\x0c\x44\x65\x62ugModeMsg\x12\"\n\x04mode\x18\x01 \x01(\x0e\x32\x14.pilot_api.DebugMode\"\x9c\x01\n\tMetricMsg\x12\x0e\n\x04\x62ool\x18\x01 \x01(\x08H\x00\x12\x10\n\x06\x64ouble\x18\x02 \x01(\x01H\x00\x12\x0f\n\x05\x66loat\x18\x03 \x01(\x02H\x00\x12\x0f\n\x05int32\x18\x04 \x01(\x11H\x00\x12\x0f\n\x05int64\x18\x05 \x01(\x12H\x00\x12\x10\n\x06uint32\x18\x06 \x01(\rH\x00\x12\x10\n\x06uint64\x18\x07 \x01(\x04H\x00\x12\r\n\x03str\x18\x08 \x01(\tH\x00\x42\x07\n\x05value\"\xc7\x03\n\nMetricInfo\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x15\n\rfriendly_name\x18\x03 \x01(\t\x12\'\n\x06\x63onfig\x18\x04 \x01(\x0e\x32\x17.pilot_api.MetricConfig\x12*\n\x0bmetric_type\x18\x05 \x01(\x0e\x32\x15.pilot_api.MetricType\x12\x10\n\x08location\x18\x06 \x01(\t\x12\x30\n\x0b\x64\x61ta_source\x18\x07 \x01(\x0e\x32\x1b.pilot_api.MetricDataSource\x12.\n\rmetric_source\x18\x08 \x01(\x0e\x32\x17.pilot_api.MetricSource\x12\x13\n\x0b\x64\x65scription\x18\t \x01(\t\x12\x10\n\x08writable\x18\n \x01(\x08\x12\x11\n\tprecision\x18\x0b \x01(\r\x12\x0c\n\x04unit\x18\x0c \x01(\t\x12\r\n\x05group\x18\r \x01(\t\x12\x36\n\tvalue_map\x18\x0e \x03(\x0b\x32#.pilot_api.MetricInfo.ValueMapEntry\x1a/\n\rValueMapEntry\x12\x0b\n\x03key\x18\x01 \x01(\r\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"\xa5\x01\n\rMetricInfoMsg\x12$\n\x03new\x18\x01 \x01(\x0b\x32\x15.pilot_api.MetricInfoH\x00\x12\'\n\x06update\x18\x02 \x01(\x0b\x32\x15.pilot_api.MetricInfoH\x00\x12\x10\n\x06remove\x18\x03 \x01(\tH\x00\x12+\n\x05\x65vent\x18\x04 \x01(\x0e\x32\x1a.pilot_api.MetricInfoEventH\x00\x42\x06\n\x04info\"\"\n\x10\x46wConfigResponse\x12\x0e\n\x06\x63onfig\x18\x01 \x01(\t\"(\n\nIdResponse\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04uuid\x18\x02 \x01(\t\"C\n\x0eNamedMetricMsg\x12\x0b\n\x03key\x18\x01 \x01(\t\x12$\n\x06metric\x18\x02 \x01(\x0b\x32\x14.pilot_api.MetricMsg\"q\n\x0f\x46irmwareRequest\x12)\n\x06target\x18\x01 \x01(\x0e\x32\x19.pilot_api.FirmwareTarget\x12\x0e\n\x06\x62inary\x18\x02 \x01(\x0c\x12\x11\n\tvariables\x18\x03 \x01(\t\x12\x10\n\x08\x66wconfig\x18\x04 \x01(\t\"\"\n\x0e\x46irmwareStatus\x12\x10\n\x08progress\x18\x01 \x01(\r\"k\n\rMetricRequest\x12*\n\x04name\x18\x01 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x12.\n\trateLimit\x18\x02 \x01(\x0b\x32\x1b.google.protobuf.FloatValue*9\n\tDebugMode\x12\x0c\n\x08\x44\x65\x62ugOff\x10\x00\x12\x10\n\x0c\x44\x65\x62ugModules\x10\x01\x12\x0c\n\x08\x44\x65\x62ugAll\x10\x02*\"\n\x0cMetricSource\x12\x06\n\x02Io\x10\x00\x12\n\n\x06Sensor\x10\x01*k\n\x0cMetricConfig\x12\x0f\n\x0bUnavailable\x10\x00\x12\x0b\n\x07Unknown\x10\x01\x12\x08\n\x04None\x10\x02\x12\x0e\n\nSubscribed\x10\x03\x12\n\n\x06\x46orced\x10\x04\x12\x17\n\x13\x46orcedAndSubscribed\x10\x05*\x84\x01\n\x10MetricDataSource\x12\x12\n\x0eUartDebugMode0\x10\x00\x12\x12\n\x0eUartDebugMode1\x10\x01\x12\x12\n\x0eUartDebugMode2\x10\x02\x12\x0f\n\x0bPilotStream\x10\x03\x12\x12\n\x0eUartNexusPower\x10\x04\x12\x07\n\x03I2c\x10\x05\x12\x06\n\x02\x46s\x10\x06*-\n\x0fMetricInfoEvent\x12\x0f\n\x0bInitialDone\x10\x00\x12\t\n\x05\x43lear\x10\x01*w\n\nMetricType\x12\x08\n\x04\x42ool\x10\x00\x12\x06\n\x02U8\x10\x01\x12\x07\n\x03U16\x10\x02\x12\x07\n\x03U32\x10\x03\x12\x07\n\x03U64\x10\x04\x12\x06\n\x02I8\x10\x05\x12\x07\n\x03I16\x10\x06\x12\x07\n\x03I32\x10\x07\x12\x07\n\x03I64\x10\x08\x12\x07\n\x03\x46\x33\x32\x10\t\x12\x07\n\x03\x46\x36\x34\x10\n\x12\x07\n\x03Str\x10\x0b*4\n\x0e\x46irmwareTarget\x12\x12\n\x0ePilotMainboard\x10\x00\x12\x0e\n\nSmartPower\x10\x01\x32\xdb\x03\n\x08PilotApi\x12\x42\n\x0bGetFwConfig\x12\x16.google.protobuf.Empty\x1a\x1b.pilot_api.FwConfigResponse\x12\x36\n\x05GetID\x12\x16.google.protobuf.Empty\x1a\x15.pilot_api.IdResponse\x12\x43\n\x07SetName\x12\x1c.google.protobuf.StringValue\x1a\x1a.google.protobuf.BoolValue\x12\x43\n\rGetMetricInfo\x12\x16.google.protobuf.Empty\x1a\x18.pilot_api.MetricInfoMsg0\x01\x12=\n\tGetMetric\x12\x18.pilot_api.MetricRequest\x1a\x14.pilot_api.MetricMsg0\x01\x12\x42\n\tSetMetric\x12\x19.pilot_api.NamedMetricMsg\x1a\x1a.google.protobuf.BoolValue\x12\x46\n\x0bSetFirmware\x12\x1a.pilot_api.FirmwareRequest\x1a\x19.pilot_api.FirmwareStatus0\x01\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'pilot_api_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _METRICINFO_VALUEMAPENTRY._options = None
  _METRICINFO_VALUEMAPENTRY._serialized_options = b'8\001'
  _DEBUGMODE._serialized_start=1335
  _DEBUGMODE._serialized_end=1392
  _METRICSOURCE._serialized_start=1394
  _METRICSOURCE._serialized_end=1428
  _METRICCONFIG._serialized_start=1430
  _METRICCONFIG._serialized_end=1537
  _METRICDATASOURCE._serialized_start=1540
  _METRICDATASOURCE._serialized_end=1672
  _METRICINFOEVENT._serialized_start=1674
  _METRICINFOEVENT._serialized_end=1719
  _METRICTYPE._serialized_start=1721
  _METRICTYPE._serialized_end=1840
  _FIRMWARETARGET._serialized_start=1842
  _FIRMWARETARGET._serialized_end=1894
  _DEBUGMODEMSG._serialized_start=91
  _DEBUGMODEMSG._serialized_end=141
  _METRICMSG._serialized_start=144
  _METRICMSG._serialized_end=300
  _METRICINFO._serialized_start=303
  _METRICINFO._serialized_end=758
  _METRICINFO_VALUEMAPENTRY._serialized_start=711
  _METRICINFO_VALUEMAPENTRY._serialized_end=758
  _METRICINFOMSG._serialized_start=761
  _METRICINFOMSG._serialized_end=926
  _FWCONFIGRESPONSE._serialized_start=928
  _FWCONFIGRESPONSE._serialized_end=962
  _IDRESPONSE._serialized_start=964
  _IDRESPONSE._serialized_end=1004
  _NAMEDMETRICMSG._serialized_start=1006
  _NAMEDMETRICMSG._serialized_end=1073
  _FIRMWAREREQUEST._serialized_start=1075
  _FIRMWAREREQUEST._serialized_end=1188
  _FIRMWARESTATUS._serialized_start=1190
  _FIRMWARESTATUS._serialized_end=1224
  _METRICREQUEST._serialized_start=1226
  _METRICREQUEST._serialized_end=1333
  _PILOTAPI._serialized_start=1897
  _PILOTAPI._serialized_end=2372
# @@protoc_insertion_point(module_scope)
