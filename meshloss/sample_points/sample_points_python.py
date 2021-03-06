import open3d
# ATTENTION! open3d have to be imported before pytorch
import torch
import numpy as np
from torch.distributions.categorical import Categorical


class PointSampler(torch.nn.Module):
    def __init__(self, point_num):
        super(PointSampler, self).__init__()
        self.point_num = point_num

    def sample_surfaces(self, vertices, faces, point_num):
        triangles = vertices[faces]
        vec1 = triangles[:, 1, :] - triangles[:, 0, :]
        vec2 = triangles[:, 2, :] - triangles[:, 0, :]
        normals = torch.cross(vec1, vec2)

        areas = torch.norm(normals, dim=1) / 2

        m = Categorical(areas)

        indices = m.sample((point_num,))
        samples_triangles = triangles[indices]

        normals = normals / (areas.reshape(-1, 1) * 2)
        samples_normals = normals[indices]

        return samples_triangles, samples_normals

    def get_normal(self, triangles):
        pass

    def forward(self, vertices_batch: torch.Tensor, faces_batch: torch.Tensor):
        point_cloud_batch = []
        normal_batch = []
        # randomly select surface
        for vertices, faces in zip(vertices_batch, faces_batch):
            sampled_triangles, sampled_normals = self.sample_surfaces(vertices.float(), faces.long(), self.point_num)
            epsilon1_arr = torch.FloatTensor(self.point_num).uniform_(0, 1)
            epsilon2_arr = torch.FloatTensor(self.point_num).uniform_(0, 1)

            epsilon1_arr = epsilon1_arr.to(vertices_batch.device)
            epsilon2_arr = epsilon2_arr.to(vertices_batch.device)

            sqrt_epsilon1 = torch.sqrt(epsilon1_arr)

            w1 = 1 - sqrt_epsilon1
            w2 = (1 - epsilon2_arr) * sqrt_epsilon1
            w3 = epsilon2_arr * sqrt_epsilon1

            w1w2w3 = torch.stack([w1, w2, w3]).transpose(0, 1).reshape(self.point_num, 3, 1)

            result = sampled_triangles * w1w2w3
            result = torch.sum(result, dim=1)
            point_cloud_batch.append(result)
            normal_batch.append(sampled_normals)
        return torch.stack(point_cloud_batch), torch.stack(normal_batch)


def test2():
    mesh: open3d.geometry.TriangleMesh = open3d.io.read_triangle_mesh(filename='../tmp/model_normalized.obj')
    faces = np.asarray(mesh.triangles)
    vertices = np.asarray(mesh.vertices)

    faces = torch.from_numpy(faces).long()

    vertices = torch.from_numpy(vertices).float()
    vertices.requires_grad = True

    triangles = vertices[faces]
    vec1 = triangles[:, 1, :] - triangles[:, 0, :]
    vec2 = triangles[:, 2, :] - triangles[:, 0, :]
    normals = torch.cross(vec1, vec2)
    areas = torch.norm(normals, dim=1) / 2

    normals = normals / (areas.reshape(-1, 1) * 2)

    m = Categorical(areas)

    indices = m.sample(sample_shape=(4,))

    triangles_sampled = triangles[indices]

    print(normals[indices])


def test1():
    point_len = 2000
    mesh: open3d.geometry.TriangleMesh = open3d.io.read_triangle_mesh(filename='../tmp/model_normalized.obj')
    faces = np.asarray(mesh.triangles)
    vertices = np.asarray(mesh.vertices)

    faces = torch.from_numpy(faces).long()

    vertices = torch.from_numpy(vertices).float()
    vertices.requires_grad = True

    triangles = vertices[faces]
    vec1 = triangles[:, 1, :] - triangles[:, 0, :]
    vec2 = triangles[:, 2, :] - triangles[:, 0, :]
    areas = torch.norm(torch.cross(vec1, vec2), dim=1) / 2

    m = Categorical(areas)

    indices = m.sample(sample_shape=(point_len,))

    triangles_sampled = triangles[indices]

    print(triangles_sampled)

    epsilon1_arr = torch.FloatTensor(point_len).uniform_(0, 1)
    epsilon2_arr = torch.FloatTensor(point_len).uniform_(0, 1)

    sqrt_epsilon1 = torch.sqrt(epsilon1_arr)

    w1 = 1 - sqrt_epsilon1
    w2 = (1 - epsilon2_arr) * sqrt_epsilon1
    w3 = epsilon2_arr * sqrt_epsilon1

    w1w2w3 = torch.stack([w1, w2, w3]).transpose(0, 1).reshape(point_len, 3, 1)

    result = (triangles_sampled * w1w2w3).sum(dim=1)
    print(result)

    # visualization
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    result: np.ndarray = result.detach().numpy()
    result = result.transpose()
    ax.scatter(result[0], result[1], result[2])

    # triangles_np: np.ndarray = triangles_sampled.detach().numpy()
    # triangles_np = triangles_np.reshape((-1, 3)).transpose()
    # ax.scatter(triangles_np[0], triangles_np[1], triangles_np[2], marker='^')
    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')
    plt.show()


if __name__ == '__main__':
    test1()
