import numpy as np

from .coordinate_transform import cartesian_3D_to_lonlat


def get_Icosahedron_vertices():
    phi = (1 + np.sqrt(5)) / 2
    vertices = np.array(
        [
            (phi, 1, 0),
            (phi, -1, 0),
            (-phi, -1, 0),
            (-phi, 1, 0),
            (1, 0, phi),
            (-1, 0, phi),
            (-1, 0, -phi),
            (1, 0, -phi),
            (0, phi, 1),
            (0, phi, -1),
            (0, -phi, -1),
            (0, -phi, 1),
        ]
    )
    return vertices


def calc_and_judge_distance(v1, v2, v3):
    d1 = np.sum((np.array(v1) - np.array(v2)) ** 2) ** (1 / 2)
    d2 = np.sum((np.array(v1) - np.array(v3)) ** 2) ** (1 / 2)
    d3 = np.sum((np.array(v2) - np.array(v3)) ** 2) ** (1 / 2)
    if d1 == d2 == d3 == 2:
        return True
    else:
        return False


def get_Icosahedron_faces():
    vertices = get_Icosahedron_vertices()

    face_list = []
    for vertice1 in vertices:
        for vertice2 in vertices:
            for vertice3 in vertices:
                same_face = calc_and_judge_distance(vertice1, vertice2, vertice3)
                if same_face:
                    the_face_set = set([tuple(vertice1), tuple(vertice2), tuple(vertice3)])
                    if the_face_set not in face_list:
                        face_list.append(the_face_set)

    face_list = np.array([list(i) for i in face_list])
    return face_list


def get_earth_Icosahedron_vertices_and_faces():
    # earth_radius_km=6371.0
    # get Icosahedron vertices and faces
    vertices = get_Icosahedron_vertices()
    face_list = get_Icosahedron_faces()

    # Scale: from 2 to 6371
    # scale_ori = (np.sum(vertices**2, axis=1)**(1/2))[0]
    # # Scale vertices and face_list to km
    # vertices = vertices * (earth_radius_km/scale_ori)
    # face_list = face_list * (earth_radius_km/scale_ori)

    vertices_lng, vertices_lat = cartesian_3D_to_lonlat(vertices[:, 0], vertices[:, 1], vertices[:, 2])

    faces_lng, faces_lat = cartesian_3D_to_lonlat(face_list[:, :, 0], face_list[:, :, 1], face_list[:, :, 2])

    return np.stack([vertices_lng, vertices_lat], axis=-1), np.stack([faces_lng, faces_lat], axis=-1)
