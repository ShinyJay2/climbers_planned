# import 항목
import os
import math
import random

from numpy import square

# from matplotlib import pyplot as plt

from . import models as travels_models

# aco 코드
class SolveTSPUsingACO:
    class Edge:  # Edge(node)
        def __init__(self, a, b, weight=0, initial_pheromone=0):
            self.a = a  # Y 좌표
            self.b = b  # X 좌표
            self.weight = weight
            self.pheromone = initial_pheromone  # 현재 길에 뿌려져있는 페로몬 양

    class Ant:  # Ant
        def __init__(self, alpha, beta, num_nodes, edges):
            self.alpha = alpha
            self.beta = beta
            self.num_nodes = num_nodes
            self.edges = edges
            self.tour = None
            self.distance = 0.0

        def _select_node(self):  # Node 선택
            roulette_wheel = 0.0  # 룰렛 휠
            unvisited_nodes = [
                node for node in range(self.num_nodes) if node not in self.tour
            ]  # 방문하지 않은 노드
            heuristic_total = 0.0
            for unvisited_node in unvisited_nodes:
                heuristic_total += self.edges[self.tour[-1]][unvisited_node].weight
            for unvisited_node in unvisited_nodes:
                # pow(x, y) = x의 y승
                roulette_wheel += pow(
                    self.edges[self.tour[-1]][unvisited_node].pheromone, self.alpha
                ) * pow(
                    (
                        heuristic_total
                        / self.edges[self.tour[-1]][unvisited_node].weight
                    ),
                    self.beta,
                )
            random_value = random.uniform(
                0.0, roulette_wheel
            )  # 0.0과 roulette_wheel 사이의 랜덤한 실수 반환
            wheel_position = 0.0
            for unvisited_node in unvisited_nodes:
                wheel_position += pow(
                    self.edges[self.tour[-1]][unvisited_node].pheromone, self.alpha
                ) * pow(
                    (
                        heuristic_total
                        / self.edges[self.tour[-1]][unvisited_node].weight
                    ),
                    self.beta,
                )
                if wheel_position >= random_value:
                    return unvisited_node

        # tour 하는 함수
        def find_tour(self):
            # 첫번째 노드는 랜덤함
            self.tour = [random.randint(0, self.num_nodes - 1)]
            while len(self.tour) < self.num_nodes:
                # select_node에서 노드를 선택하여 tour list에 저장
                self.tour.append(self._select_node())
            return self.tour

        # 총 이동거리를 가져옴
        def get_distance(self):
            self.distance = 0.0
            for i in range(self.num_nodes):
                self.distance += self.edges[self.tour[i]][
                    self.tour[(i + 1) % self.num_nodes]
                ].weight
            return self.distance

    def __init__(
        self,
        mode="MaxMin",
        colony_size=10,
        elitist_weight=1.0,
        min_scaling_factor=0.001,
        alpha=1.0,
        beta=3.0,
        rho=0.1,
        pheromone_deposit_weight=1.0,
        initial_pheromone=1.0,
        steps=100,
        nodes=None,
        labels=None,
    ):  # 초기설정
        # rho만큼의 페로몬이 삭제됨. 즉 1.0-self.rho만큼의 페로몬만 남게됨
        self.mode = mode  # 여기서는 min_max로 돌림
        self.colony_size = colony_size
        self.elitist_weight = elitist_weight
        self.min_scaling_factor = (
            min_scaling_factor  # 이 변수에 의해 max_pheromone 대비 min_pheromone 을 정함
        )
        self.rho = rho
        self.pheromone_deposit_weight = pheromone_deposit_weight
        self.steps = steps
        self.num_nodes = len(nodes)  # 노드 개수
        self.nodes = nodes
        if labels is not None:
            self.labels = labels
        else:
            self.labels = range(1, self.num_nodes + 1)
        self.edges = [[None] * self.num_nodes for _ in range(self.num_nodes)]
        for i in range(self.num_nodes):  # 행렬에 edge 값 저장
            for j in range(i + 1, self.num_nodes):
                self.edges[i][j] = self.edges[j][i] = self.Edge(
                    i,
                    j,
                    self.distance_by_haversine(self, i, j),  # weight, 거리
                    initial_pheromone,
                )
        self.ants = [
            self.Ant(alpha, beta, self.num_nodes, self.edges)
            for _ in range(self.colony_size)
        ]  # colony_size만큼 ant 생성
        self.global_best_tour = None
        self.global_best_distance = float("inf")

    def _add_pheromone(self, tour, distance, weight=1.0):  # 페로몬 뿌리기
        pheromone_to_add = self.pheromone_deposit_weight / distance
        for i in range(self.num_nodes):
            self.edges[tour[i]][tour[(i + 1) % self.num_nodes]].pheromone += (
                weight * pheromone_to_add
            )

    def _max_min(self):  # max_min 방식 사용
        for step in range(self.steps):
            iteration_best_tour = None
            iteration_best_distance = float("inf")
            # 각각의 개미들이 tour함
            for ant in self.ants:
                ant.find_tour()
                # 어떠한 개미가 지나온 길이 iteration_best_distance 보다 짧다면
                # 그 개미가 지나온 길을 저장
                if ant.get_distance() < iteration_best_distance:
                    iteration_best_tour = ant.tour
                    iteration_best_distance = ant.distance
            if (
                float(step + 1) / float(self.steps) <= 0.75
            ):  # 전체 step의 3/4 이하라면 iteration_best_tour만
                self._add_pheromone(
                    iteration_best_tour, iteration_best_distance
                )  # 페로몬 뿌리기
                max_pheromone = self.pheromone_deposit_weight / iteration_best_distance
            else:  # 전체 step의 3/4 이상이면 iteration과 global best tour를 비교
                if (
                    iteration_best_distance < self.global_best_distance
                ):  # 거리가 더 짧으면 iteration이 best가 됨
                    self.global_best_tour = iteration_best_tour
                    self.global_best_distance = iteration_best_distance
                self._add_pheromone(
                    self.global_best_tour, self.global_best_distance
                )  # 페로몬 뿌리기
                max_pheromone = (
                    self.pheromone_deposit_weight / self.global_best_distance
                )
            min_pheromone = max_pheromone * self.min_scaling_factor
            for i in range(self.num_nodes):  # 각각의 edge에서 페로몬을 제거해줌(rho)
                for j in range(i + 1, self.num_nodes):
                    # initial은 rho=0.1이기 때문에 기존 페로몬 양의 0.9만 가지게 됨
                    self.edges[i][j].pheromone *= 1.0 - self.rho
                    # 이전에 계산한 max_pheromone, min_pheromone 내에 pheromone이 있게 함
                    if self.edges[i][j].pheromone > max_pheromone:
                        self.edges[i][j].pheromone = max_pheromone
                    elif self.edges[i][j].pheromone < min_pheromone:
                        self.edges[i][j].pheromone = min_pheromone

    def run(self):
        print("Started : {0}".format(self.mode))
        self._max_min()
        print("Ended : {0}".format(self.mode))
        print(
            "Sequence : <- {0} ->".format(
                " - ".join(str(self.labels[i]) for i in self.global_best_tour)
            )
        )
        print(
            "Total distance travelled to complete the tour : {0}\n".format(
                round(self.global_best_distance, 2)
            )
        )

    def distance_by_haversine(self, i, j):
        radius = 6371  # 지구 반지름
        radian = math.pi / 180
        delta_latitude = math.abs(self.nodes[i][0] - self.nodes[j][0]) * radian
        delta_longitude = math.abs(self.nodes[i][1] - self.nodes[j][1]) * radian

        sin_delta_latitude = math.sin(delta_latitude / 2)
        sin_delta_longitude = math.sin(delta_longitude / 2)
        square_root = math.sqrt(
            sin_delta_latitude * sin_delta_latitude
            + math.cos(self.nodes[i][0] * radian)
            * math.cos(self.nodes[j][0] * radian)
            * sin_delta_longitude
            * sin_delta_longitude
        )
        return 2 * radius * math.asin(square_root)

    def save_route(self):
        num = 0
        for i in self.global_best_tour:
            place_pk = self.nodes[i][2]
            place = travels_models.Place.objects.get(pk=place_pk)
            place.order = num
            place.save()
            num += 1

    # def plot(
    #     self,
    #     line_width=1,
    #     point_radius=math.sqrt(2.0),
    #     annotation_size=8,
    #     dpi=120,
    #     save=True,
    #     name=None,
    # ):  # 사진 그래프로 보여줌
    #     x = [self.nodes[i][0] for i in self.global_best_tour]
    #     x.append(x[0])
    #     y = [self.nodes[i][1] for i in self.global_best_tour]
    #     y.append(y[0])
    #     plt.plot(x, y, linewidth=line_width)
    #     plt.scatter(x, y, s=math.pi * (point_radius**2.0))
    #     plt.title(self.mode)
    #     for i in self.global_best_tour:
    #         plt.annotate(self.labels[i], self.nodes[i], size=annotation_size)
    #     if save:
    #         if name is None:
    #             name = "{0}.png".format(self.mode)
    #         plt.savefig(name, dpi=dpi)
    #     plt.show()
    #     plt.gcf().clear()


def aco_run(travel, count_date):
    all_places = travels_models.Place.objects.filter(travel=travel)
    for i in range(1, count_date + 1):
        node_places = all_places.filter(day=i)
        _colony_size = 5
        _steps = 50  # 몇번의 step으로 결과를 낼 것인지
        _nodes = [(place.latitude, place.longitude, place.pk) for place in node_places]
        max_min = SolveTSPUsingACO(
            mode="MaxMin", colony_size=_colony_size, steps=_steps, nodes=_nodes
        )
        max_min.run()
        # max_min.plot()
        max_min.save_route()


# if __name__ == "__main__":
#     _colony_size = 5
#     _steps = 50
#     _nodes = [
#         (random.uniform(-400, 400), random.uniform(-400, 400)) for _ in range(0, 15)
#     ]  # 여기에 place 값 가져오면 될 듯
#     max_min = SolveTSPUsingACO(
#         mode="MaxMin", colony_size=_colony_size, steps=_steps, nodes=_nodes
#     )
#     max_min.run()
#     max_min.plot()
