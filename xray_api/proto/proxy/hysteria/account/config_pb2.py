# Schema from XTLS/Xray-core v26.3.27 proxy/hysteria/account/config.proto.
# Construct the descriptor at runtime to support the project's protobuf runtime.
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

_file = descriptor_pb2.FileDescriptorProto(
    name="proxy/hysteria/account/config.proto",
    package="xray.proxy.hysteria.account", syntax="proto3",
)
_message = _file.message_type.add(name="Account")
_message.field.add(name="auth", number=1, label=1, type=9)
DESCRIPTOR = descriptor_pool.Default().AddSerializedFile(_file.SerializeToString())
Account = message_factory.GetMessageClass(DESCRIPTOR.message_types_by_name["Account"])
