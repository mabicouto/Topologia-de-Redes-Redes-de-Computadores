import ipaddress
import random
import networkx as nx
import matplotlib.pyplot as plt
import time

# Função para simular o ping
def simular_ping():
    return random.randint(10, 200)  # Simulando latência entre 10ms e 200ms

# Função para gerar os endereços IP de uma sub-rede
def alocar_enderecos(subrede, num_hosts):
    hosts = list(subrede.hosts())  # Gera os IPs disponíveis para hosts
    return hosts[:num_hosts] if len(hosts) >= num_hosts else []

# Definição das sub-redes
e1 = ipaddress.IPv4Network('192.168.1.0/27')
e2 = ipaddress.IPv4Network('192.168.1.32/27')
e3 = ipaddress.IPv4Network('192.168.1.64/27')
e4 = ipaddress.IPv4Network('192.168.1.96/27')

hosts_e1 = alocar_enderecos(e1, 24)
hosts_e2 = alocar_enderecos(e2, 24)
hosts_e3 = alocar_enderecos(e3, 15)
hosts_e4 = alocar_enderecos(e4, 15)

# Definição dos roteadores e switches
roteadores = {"RoteadorA1": "192.168.1.97", "RoteadorA2": "192.168.1.101"}
switches = {"Switch1": "192.168.1.2", "Switch2": "192.168.1.34", "Switch3": "192.168.1.66", "Switch4": "192.168.1.98"}

# Adicionando tipos de enlaces e justificativas
enlaces = {
    ("Switch1", "RoteadorA1"): {"tipo": "fibra óptica", "capacidade": "1 Gbps", "justificativa": "Alta velocidade e baixa latência para conexão central"},
    ("Switch3", "RoteadorA1"): {"tipo": "fibra óptica", "capacidade": "1 Gbps", "justificativa": "Alta velocidade e baixa latência para conexão central"},
    ("Switch2", "RoteadorA2"): {"tipo": "fibra óptica", "capacidade": "1 Gbps", "justificativa": "Alta velocidade e baixa latência para conexão central"},
    ("Switch4", "RoteadorA2"): {"tipo": "fibra óptica", "capacidade": "1 Gbps", "justificativa": "Alta velocidade e baixa latência para conexão central"},
}

# Tabelas de roteamento estáticas
tabelas_roteamento = {
    "RoteadorA1": {
        "192.168.1.0/27": "Switch1",
        "192.168.1.32/27": "Switch2",
        "192.168.1.64/27": "Switch3",
        "192.168.1.96/27": "Switch4"
    },
    "RoteadorA2": {
        "192.168.1.0/27": "Switch1",
        "192.168.1.32/27": "Switch2",
        "192.168.1.64/27": "Switch3",
        "192.168.1.96/27": "Switch4"
    }
}

def mostrar_tabelas_roteamento(G):
    print("\nTabelas de Roteamento:")
    for roteador, tabela in tabelas_roteamento.items():
        print(f"\n{roteador}:")
        for rede, proximo_salto in tabela.items():
            print(f"  {rede} -> {proximo_salto}")
    
    print("\nEndereços IP de todos os hosts no grafo:")
    for node, data in G.nodes(data=True):
        if data.get('type') == 'host':  # Filtra apenas os nós do tipo 'host'
            print(f"  {node}: {data.get('ip')}")

def menu_interativo(G):
    while True:
        comando = input("\nDigite um comando (ping <IP>, tabelas, sair, traceroute): ").strip().lower()
        
        if comando.startswith("ping"):
            _, destino_ip = comando.split(maxsplit=1)
            ping_terminal(G, destino_ip)
        elif comando == "tabelas":
            mostrar_tabelas_roteamento(G)
        elif comando == "sair":
            print("Encerrando o programa...")
            plt.close()  # Fecha a janela do gráfico
            break
        elif comando.startswith("traceroute"):
            _, destino_ip = comando.split(maxsplit=1)
            traceroute(G, destino_ip, e1, e2, e3, e4)
        else:
            print("Comando inválido. Tente novamente.")


def ping_terminal(G, destino_ip):
    origem = list(G.nodes())[0]  # Assume o primeiro nó como origem
    destino = None

    # Verifica se o IP de destino existe no grafo
    for node, data in G.nodes(data=True):
        if data.get('ip') == destino_ip:
            destino = node
            break

    if not destino:
        print(f"Host {destino_ip} não encontrado na rede.")
        return

    print(f"Disparando ping em {destino_ip} com 32 bytes de dados:")

    pacotes_enviados = 4
    pacotes_recebidos = 0
    tempos = []

    for _ in range(pacotes_enviados):
        try:
            # Tenta encontrar o caminho mais curto entre origem e destino
            caminho = nx.shortest_path(G, source=origem, target=destino, weight='weight')
            # Calcula a latência total do caminho
            latencia_total = sum(G[u][v]['weight'] for u, v in zip(caminho[:-1], caminho[1:]))
            print(f"Resposta de {destino_ip}: bytes=32 tempo={latencia_total}ms TTL={random.randint(50, 128)}")
            pacotes_recebidos += 1
            tempos.append(latencia_total)
        except nx.NetworkXNoPath:
            print("Esgotado o tempo limite do pedido.")
        time.sleep(1)

    perda = ((pacotes_enviados - pacotes_recebidos) / pacotes_enviados) * 100
    print(f"\nEstatísticas do Ping para {destino_ip}:")
    print(f"    Pacotes: Enviados = {pacotes_enviados}, Recebidos = {pacotes_recebidos}, Perdidos = {pacotes_enviados - pacotes_recebidos} ({int(perda)}% de perda)")

    if tempos:
        print(f"Aproximar um número redondo de tempos em milissegundos:")
        print(f"    Mínimo = {min(tempos)}ms, Máximo = {max(tempos)}ms, Média = {sum(tempos)//len(tempos)}ms")
        
def traceroute(G, destino_ip, e1, e2, e3, e4, max_hops=30):
    try:
        destino_ip_obj = ipaddress.IPv4Address(destino_ip)
    except ValueError:
        print(f"Erro: O IP {destino_ip} não é um endereço IPv4 válido.")
        return

    # Define a origem com base na sub-rede do destino
    if destino_ip_obj in e1 or destino_ip_obj in e3:
        origem = "RoteadorA1"  # Origem para sub-redes gerenciadas pelo RoteadorA1
    elif destino_ip_obj in e2 or destino_ip_obj in e4:
        origem = "RoteadorA2"  # Origem para sub-redes gerenciadas pelo RoteadorA2
    else:
        print(f"Erro: O IP {destino_ip} não pertence a nenhuma sub-rede conhecida.")
        return

    destino = None

    # Busca o destino no grafo
    for node, data in G.nodes(data=True):
        if data.get('ip') == destino_ip:
            destino = node
            break

    if not destino:
        print(f"Erro: O IP {destino_ip} não foi encontrado na rede.")
        return

    print(f"\nRastreando rota para {destino_ip} a partir de {origem}...\n")

    try:
        # Verifica se há um caminho entre a origem e o destino
        if not nx.has_path(G, source=origem, target=destino):
            print("Erro: Não há caminho entre a origem e o destino. Verifique a conectividade.")
            return

        caminho = nx.shortest_path(G, source=origem, target=destino, weight='weight')
        print("Caminho encontrado:", caminho)  # Mostra os nós pelo qual o pacote está passando
        total_saltos = min(len(caminho), max_hops)

        for i in range(total_saltos):
            nodo_atual = caminho[i]
            latencia = sum(G[u][v]['weight'] for u, v in zip(caminho[:i], caminho[1:i+1])) if i > 0 else 0
            ttl = max_hops - i  # Simulando TTL decrescente
            
            print(f"{i+1}\t{G.nodes[nodo_atual].get('ip', 'Desconhecido')}\t{latencia}ms\tTTL={ttl}")
            time.sleep(0.5)

    except nx.NetworkXNoPath:
        print("Erro: Não há caminho entre a origem e o destino. Verifique a conectividade.")

    print("\nRastreamento concluído.")
    
def diagnostico_completo():
    print("\nIniciando diagnóstico de rede...")
    # Diagnóstico completo omitido para foco no ping


def plotar_rede():
    G = nx.Graph()
    
    # Adicionando nós
    for nome, ip in {**roteadores, **switches}.items():
        G.add_node(nome, type='dispositivo', ip=ip)
    for i, host in enumerate(hosts_e1 + hosts_e2 + hosts_e3 + hosts_e4):
        G.add_node(f"Host{i+1}", type='host', ip=str(host))
    
    # Conexões entre dispositivos
    conexoes = [
        ("Switch1", "RoteadorA1"),
        ("Switch3", "RoteadorA1"),
        ("Switch2", "RoteadorA2"),
        ("Switch4", "RoteadorA2")
    ]
    for i in range(24):
        conexoes.append((f"Host{i+1}", "Switch1"))
    for i in range(24):
        conexoes.append((f"Host{i+25}", "Switch2"))
    for i in range(15):
        conexoes.append((f"Host{i+49}", "Switch3"))
    for i in range(15):
        conexoes.append((f"Host{i+64}", "Switch4"))
    
    # Adicionando arestas com latência simulada e informações de enlace
    for origem, destino in conexoes:
        latencia = simular_ping()
        tipo_enlace = enlaces.get((origem, destino), {}).get("tipo", "desconhecido")
        G.add_edge(origem, destino, weight=latencia, tipo_enlace=tipo_enlace)
    
    # Verifica se o grafo está conectado
    if not nx.is_connected(G):
        print("Aviso: O grafo não está completamente conectado. Alguns hosts podem ser inalcançáveis.")
    
    # Definir cores e tamanhos dos nós
    node_colors = ['orange' if G.nodes[n]['type'] == 'dispositivo' else 'lightblue' for n in G.nodes]
    node_sizes = [1000 if G.nodes[n]['type'] == 'dispositivo' else 500 for n in G.nodes]
    
    # Layout e visualização
    plt.figure(figsize=(12, 12))
    pos = nx.spring_layout(G, seed=42)
    nx.draw(G, pos, with_labels=True, node_size=node_sizes, node_color=node_colors, font_size=8, edge_color='gray')
    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    
    plt.title("Topologia da Rede com Latência do Ping")
    plt.show(block=False)  # Não bloquear a execução do programa
    plt.pause(0.1)  # Pausa para garantir que a janela seja renderizada

    return G


def menu_interativo(G):
    while True:
        comando = input("\nDigite um comando (ping <IP>, tabelas, sair, traceroute): ").strip().lower()
        
        if comando.startswith("ping"):
            _, destino_ip = comando.split(maxsplit=1)
            ping_terminal(G, destino_ip)
        elif comando == "tabelas":
            mostrar_tabelas_roteamento(G)
        elif comando == "sair":
            print("Encerrando o programa...")
            plt.close()  # Fecha a janela do gráfico
            break
        elif comando.startswith("traceroute"):
            _, destino_ip = comando.split(maxsplit=1)
            traceroute(G, destino_ip, e1, e2, e3, e4)
        else:
            print("Comando inválido. Tente novamente.")


if __name__ == "_main_":
    G = plotar_rede()
    menu_interativo(G)
