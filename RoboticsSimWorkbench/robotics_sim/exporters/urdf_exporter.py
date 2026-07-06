"""Basic URDF exporter.

Produces a structurally valid URDF from a RobotModel. Because v1 stores CAD
object *references* rather than exported meshes, visual/collision geometry
defaults to a placeholder box, but a mesh filename is emitted instead when a
link carries mesh references (``<mesh filename="meshes/<ref>.stl"/>``). Inertial
data uses placeholder values when exact mass/inertia is unavailable.

Length values are scaled by ``export_settings['length_scale']`` (default mm->m).
"""

from __future__ import annotations

import math
from typing import List

from ..document_model import RobotModel
from ..kinematics import Transform


def _fmt(x: float) -> str:
    return ("%.6g" % float(x))


def _origin_xml(tf: Transform, scale: float, indent: str) -> str:
    x, y, z = tf.translation
    r, p, yw = tf.rpy()
    return '%s<origin xyz="%s %s %s" rpy="%s %s %s"/>\n' % (
        indent, _fmt(x * scale), _fmt(y * scale), _fmt(z * scale),
        _fmt(r), _fmt(p), _fmt(yw),
    )


def _geometry_xml(refs: List[str], mesh_dir: str, scale: float, indent: str) -> str:
    if refs:
        # Reference a mesh per the first geometry ref (practical placeholder).
        fname = "%s/%s.stl" % (mesh_dir.rstrip("/"), refs[0])
        return '%s<geometry><mesh filename="%s"/></geometry>\n' % (indent, fname)
    # Placeholder unit box (already in meters).
    return '%s<geometry><box size="0.1 0.1 0.1"/></geometry>\n' % indent


def _inertial_xml(link, scale: float, indent: str) -> str:
    ixx, ixy, ixz, iyy, iyz, izz = link.inertia
    out = "%s<inertial>\n" % indent
    out += "%s  <origin xyz=\"0 0 0\" rpy=\"0 0 0\"/>\n" % indent
    out += "%s  <mass value=\"%s\"/>\n" % (indent, _fmt(link.mass))
    out += (
        "%s  <inertia ixx=\"%s\" ixy=\"%s\" ixz=\"%s\" iyy=\"%s\" iyz=\"%s\" izz=\"%s\"/>\n"
        % (indent, _fmt(ixx), _fmt(ixy), _fmt(ixz), _fmt(iyy), _fmt(iyz), _fmt(izz))
    )
    out += "%s</inertial>\n" % indent
    return out


def export_urdf(model: RobotModel) -> str:
    scale = model.export_settings.get("length_scale", 0.001)
    mesh_dir = model.export_settings.get("urdf_mesh_dir", "meshes")
    lines = ['<?xml version="1.0"?>']
    lines.append('<robot name="%s">' % model.name)

    for link in model.links.values():
        lines.append('  <link name="%s">' % link.name)
        block = _inertial_xml(link, scale, "    ")
        block += "    <visual>\n"
        block += _geometry_xml(link.visual_refs, mesh_dir, scale, "      ")
        block += "    </visual>\n"
        block += "    <collision>\n"
        block += _geometry_xml(link.collision_refs, mesh_dir, scale, "      ")
        block += "    </collision>\n"
        lines.append(block.rstrip("\n"))
        lines.append("  </link>")

    for joint in model.joints.values():
        lines.append('  <joint name="%s" type="%s">' % (joint.name, joint.type))
        lines.append('    <parent link="%s"/>' % joint.parent_link)
        lines.append('    <child link="%s"/>' % joint.child_link)
        lines.append(_origin_xml(joint.origin, scale, "    ").rstrip("\n"))
        if joint.type != "fixed":
            ax = joint.axis
            lines.append('    <axis xyz="%s %s %s"/>' % (_fmt(ax[0]), _fmt(ax[1]), _fmt(ax[2])))
            lo = joint.lower_limit
            hi = joint.upper_limit
            # prismatic limits are lengths -> scale; revolute are radians -> as-is
            if joint.type == "prismatic":
                lo, hi = lo * scale, hi * scale
            effort = joint.effort_limit if joint.effort_limit is not None else 100.0
            lines.append('    <limit lower="%s" upper="%s" effort="%s" velocity="1.0"/>'
                         % (_fmt(lo), _fmt(hi), _fmt(effort)))
        lines.append("  </joint>")

    lines.append("</robot>")
    return "\n".join(lines) + "\n"


def write_urdf(model: RobotModel, path: str) -> str:
    text = export_urdf(model)
    with open(path, "w") as fh:
        fh.write(text)
    return path
