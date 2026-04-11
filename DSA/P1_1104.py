#DFS and BFS 

from  collections import deque

#BFS
def bfs(graph, start):
    visited = set()
    queue = deque([start])
    visited.add(start)
    print("BFS Traversal:", end=" ")
    while queue:
        node = queue.popleft()
        print(node, end=" ")
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    print()

#DFS
def dfs_iterative(graph, start):
    visited = set()
    stack = [start]
    print("DFS Traversal:", end=" ")
    while stack:
        node = stack.pop()
        if node not in visited:
            print(node, end=" ")
            visited.add(node)
            for neighbor in reversed(graph[node]):
                if neighbor not in visited:
                    stack.append(neighbor)
    print()

    

def main():
    graph = {}
    n = int(input("Enter number of nodes:"))
    print("Enter nodes:")
    nodes = []
    for _ in range(n):
        node = input()
        nodes.append(node)
        graph[node] = []
    
    e = int(input("Enter number of edges: "))
    print("Enter edges (u,v): ")
    for _ in range(e):
        u, v = input().split()
        graph[u].append(v)
        graph[v].append(u)
    
    start = input("Enter starting node: ")

    bfs(graph, start)
    dfs_iterative(graph, start)



if __name__ =="__main__":
    main()