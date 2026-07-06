"""Basic MJCF (MuJoCo XML) exporter.

Emits a structurally reasonable MJCF as a starting point for future MuJoCo
simulation. Builds the body tree from the joint graph: root links become
top-level bodies under <worldbody>, children nest under their parent link's body
with their joint declared inside. Geoms are placeholder boxes (or mesh refs when
available). Inertial data uses placeholders.

Length values scaled by ``export_settings['length_scale']`` (mm->m default).

Phase 2: emit proper <mesh> assets + collision classes once meshes are exported.
"""

from __future__ import annotations

from typing import Dict, List

from ..document_model import RobotModel
from ..kinematics import Transform, build_joint_graph


def _fmt(x: float) -> str:
    return ("%.6g" % float(x))


def _pos_attr(tf: Transform, scale: float) -> str:
    x, y, z = tf.translation
    return 'pos="%s %s %s"' % (_fmt(x * scale), _fmt(y * scale), _fmt(z * scale))


def _euler_attr(tf: Transform) -> str:
    r, p, yw = tf.rpy()
    return 'euler="%s %s %s"' % (_fmt(r), _fmt(p), _fmt(yw))


def _body_xml(model, link_name, children_by_link, joint_by_child, scale, indent) -> str:
    link = model.links[link_name]
    joint = joint_by_child.get(link_name)

    # Body pose = joint origin for child bodies, else stored world transform.
    if joint is not None:
        pose = joint.origin
    else:
        pose = link.world_transform

    out = '%s<body name="%s" %s %s>\n' % (
        indent, link_name, _pos_attr(pose, scale), _euler_attr(pose),
    )
    inner = indent + "  "

    if joint is not None and joint.type != "fixed":
        mj_type = "hinge" if joint.type == "revolute" else "slide"
        ax = joint.axis
        lo, hi = joint.lower_limit, joint.upper_limit
        if joint.type == "prismatic":
            lo, hi = lo * scale, hi * scale
        out += '%s<joint name="%s" type="%s" axis="%s %s %s" range="%s %s"/>\n' % (
            inner, joint.name, mj_type,
            _fmt(ax[0]), _fmt(ax[1]), _fmt(ax[2]), _fmt(lo), _fmt(hi),
        )

    # Inertial (placeholder).
    out += '%s<inertial pos="0 0 0" mass="%s" diaginertia="%s %s %s"/>\n' % (
        inner, _fmt(link.mass),
        _fmt(link.inertia[0]), _fmt(link.inertia[3]), _fmt(link.inertia[5]),
    )

    # Geom (placeholder box or mesh ref).
    if link.visual_refs:
        out += '%s<geom type="mesh" mesh="%s"/>\n' % (inner, link.visual_refs[0])
    else:
        out += '%s<geom type="box" size="0.05 0.05 0.05"/>\n' % inner

    for child_joint in children_by_link.get(link_name, []):
        out += _body_xml(model, child_joint.child_link, children_by_link,
                         joint_by_child, scale, inner)

    out += "%s</body>\n" % indent
    return out


def export_mjcf(model: RobotModel) -> str:
    scale = model.export_settings.get("length_scale", 0.001)
    children_by_link, parent_joint = build_joint_graph(model.joints.values())
    joint_by_child = {j.child_link: j for j in model.joints.values()}

    roots = [name for name in model.links if name not in parent_joint]

    # Mesh assets referenced by any link (best-effort; files may not exist yet).
    mesh_names = []
    for link in model.links.values():
        if link.visual_refs:
            m = link.visual_refs[0]
            if m not in mesh_names:
                mesh_names.append(m)

    out = '<mujoco model="%s">\n' % model.name
    out += '  <compiler angle="radian"/>\n'
    out += '  <option gravity="0 0 -9.81"/>\n'
    if mesh_names:
        mesh_dir = model.export_settings.get("mjcf_mesh_dir", "meshes")
        out += "  <asset>\n"
        for m in mesh_names:
            out += '    <mesh name="%s" file="%s/%s.stl"/>\n' % (m, mesh_dir.rstrip("/"), m)
        out += "  </asset>\n"
    out += "  <worldbody>\n"
    out += '    <geom name="ground" type="plane" size="10 10 0.1" pos="0 0 0"/>\n'
    for root in roots:
        out += _body_xml(model, root, children_by_link, joint_by_child, scale, "    ")
    out += "  </worldbody>\n"
    out += "</mujoco>\n"
    return out


def write_mjcf(model: RobotModel, path: str) -> str:
    text = export_mjcf(model)
    with open(path, "w") as fh:
        fh.write(text)
    return path
