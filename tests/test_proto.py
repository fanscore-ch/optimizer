import subprocess
from pathlib import Path

from google.protobuf import descriptor_pb2
from ortools.sat import cp_model_pb2, sat_parameters_pb2


def normalize_descriptor(message):
    # Compiler versions differ in derived JSON names and float formatting.
    for field in message.field:
        field.ClearField("json_name")
        if field.HasField("default_value") and field.type in (
            descriptor_pb2.FieldDescriptorProto.TYPE_DOUBLE,
            descriptor_pb2.FieldDescriptorProto.TYPE_FLOAT,
        ):
            field.default_value = format(float(field.default_value), ".17g")
    for nested in message.nested_type:
        normalize_descriptor(nested)


def test_vendored_protos_match_runtime(tmp_path):
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "descriptor.pb"
    subprocess.run(
        [
            "buf",
            "build",
            "--as-file-descriptor-set",
            "--exclude-source-info",
            "--output",
            str(output),
        ],
        cwd=root,
        check=True,
    )
    descriptors = descriptor_pb2.FileDescriptorSet.FromString(output.read_bytes())
    vendored = {file.name: file for file in descriptors.file}
    for module in (cp_model_pb2, sat_parameters_pb2):
        installed = descriptor_pb2.FileDescriptorProto()
        module.DESCRIPTOR.CopyToProto(installed)
        for file in (vendored[installed.name], installed):
            for message in file.message_type:
                normalize_descriptor(message)
        assert vendored[installed.name] == installed
