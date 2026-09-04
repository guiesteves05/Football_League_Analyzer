#!/usr/bin/env python3
import sys
import pulp
import gc

# Otimização para expressões complexas do PuLP que geram árvores recursivas profundas
sys.setrecursionlimit(1000000)

def fast_ints():
    # Leitura eficiente byte-a-byte para evitar carregar ficheiros grandes na RAM.
    try:
        data = sys.stdin.buffer.read()
    except Exception:
        return
    
    num = 0
    in_num = False
    for b in data:
        if 48 <= b <= 57: # ASCII para 0-9
            num = num * 10 + (b - 48)
            in_num = True
        else:
            if in_num:
                yield num
                num = 0
                in_num = False
    if in_num:
        yield num

def solve():
    iterator = fast_ints()
    try:
        n = next(iterator) # Número de equipas
        m = next(iterator) # Número de jogos já realizados
    except StopIteration:
        return
    
    # Casos Base / Edge Cases
    if n == 1:
        sys.stdout.write("0\n")
        return
    if m == 0:
        sys.stdout.write("\n".join(["0"] * n) + "\n")
        return

    # Pontos atuais de cada equipa
    curr_pts = [0] * (n + 1)
    
    # Registo de confrontos: key = par (u, v) ordenado -> valor = total de jogos feitos
    match_counts = {}

    for _ in range(m):
        try:
            u = next(iterator)
            v = next(iterator)
            r = next(iterator) # Resultado (equipa vencedora ou 0)
        except StopIteration:
            break
        
        if u < 1 or u > n or v < 1 or v > n or u == v:
            continue
        
        # Atribuição de pontos: Vitória (3), Empate (1), Derrota (0)
        if r == 0:
            curr_pts[u] += 1
            curr_pts[v] += 1
        elif r == u or r == v:
            curr_pts[r] += 3
        else:
            continue

        key = (u, v) if u < v else (v, u)
        match_counts[key] = match_counts.get(key, 0) + 1

    # Construção de Lista de Adjacência para jogos por realizar
    # Otimiza o loop principal ao visitar apenas equipas com jogos pendentes
    adj = [[] for _ in range(n + 1)]
    max_extra = [0] * (n + 1) # Máximo de pontos que uma equipa ainda pode ganhar

    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            key = (i, j)
            played = match_counts.get(key, 0)
            needed = min(2 - played, 2) # Máximo de 2 jogos por par (2 voltas)
            
            if needed > 0:
                adj[i].append((j, needed))
                adj[j].append((i, needed))
                max_extra[i] += 3 * needed
                max_extra[j] += 3 * needed

    # Teto teórico de pontos para cada equipa (Pruning)
    max_theoretical = [curr_pts[i] + max_extra[i] for i in range(n + 1)]

    # Solver CBC (Coin-or-branch-and-cut) configurado para uma única thread
    solver = pulp.PULP_CBC_CMD(msg=0, threads=1)
    
    out_buffer = []

    # Processamento equipa a equipa
    for t in range(1, n + 1):
        
        # PRUNING LÓGICO
        # Determina se é matematicamente possível a equipa 't' vencer
        my_max = max_theoretical[t]
        relevant_opponents = [] # Equipas que podem ameaçar a liderança de 't'
        impossible = False
        
        for k in range(1, n + 1):
            if k == t: continue
            
            # Se alguém já tem mais pontos agora do que 't' pode vir a ter, 't' nunca vencerá
            if curr_pts[k] > my_max:
                impossible = True
                break
            
            # Se 't' já tem mais pontos que o máximo que 'k' pode atingir, 'k' é ignorado no modelo
            if curr_pts[t] < max_theoretical[k]:
                relevant_opponents.append(k)
        
        if impossible:
            out_buffer.append("-1")
            continue
        
        if not relevant_opponents:
            out_buffer.append("0")
            continue

        # MODELAÇÃO PLI (Programação Linear Inteira) COM PuLP
        try:
            prob = pulp.LpProblem("P", pulp.LpMinimize)
            
            # Acumuladores de termos para expressões lineares de pontos
            coeffs = [[] for _ in range(n + 1)]
            base_pts = list(curr_pts)
            target_wins_vars = [] # Variáveis a minimizar (vitórias de 't')
            var_idx = 0
            relevant_set = set(relevant_opponents)

            # Modelação dos jogos da equipa alvo 't'
            for neighbor, count in adj[t]:
                xu = pulp.LpVariable(str(var_idx), 0, count, pulp.LpInteger)
                xv = pulp.LpVariable(str(var_idx+1), 0, count, pulp.LpInteger)
                var_idx += 2
                
                # xu + xv + empate = count
                prob += (xu + xv <= count)
                
                # Fórmula de pontos: 3*Vitórias + 1*Empates
                # Reescrito para usar apenas xu (vitória) e xv (derrota), considerando empate = count - xu - xv
                coeffs[t].append((xu, 2))
                coeffs[t].append((xv, -1))
                base_pts[t] += count
                
                coeffs[neighbor].append((xu, -1))
                coeffs[neighbor].append((xv, 2))
                base_pts[neighbor] += count
                
                target_wins_vars.append(xu)

            # Modelação dos jogos entre adversários diretos
            for k in relevant_opponents:
                for neighbor, count in adj[k]:
                    if neighbor == t: continue
                    
                    if neighbor in relevant_set:
                        if k < neighbor: # Evita duplicar o mesmo par de jogos
                            xu = pulp.LpVariable(str(var_idx), 0, count, pulp.LpInteger)
                            xv = pulp.LpVariable(str(var_idx+1), 0, count, pulp.LpInteger)
                            var_idx += 2
                            prob += (xu + xv <= count)
                            
                            coeffs[k].append((xu, 2))
                            coeffs[k].append((xv, -1))
                            base_pts[k] += count
                            
                            coeffs[neighbor].append((xu, -1))
                            coeffs[neighbor].append((xv, 2))
                            base_pts[neighbor] += count
                    else:
                        # Best-case: Assumimos que o adversário 'k' perde contra equipas irrelevantes
                        pass 

            # Objetivo: Minimizar as vitórias necessárias para a equipa 't'
            if target_wins_vars:
                prob += pulp.lpSum(target_wins_vars)
            else:
                prob += 0

            # Restrição: A equipa 't' tem de ficar em 1º lugar (ou empatada)
            expr_t = pulp.LpAffineExpression(coeffs[t]) + base_pts[t]
            for k in relevant_opponents:
                expr_k = pulp.LpAffineExpression(coeffs[k]) + base_pts[k]
                prob += (expr_t >= expr_k)

            # Resolução do problema linear
            status = prob.solve(solver)
            
            if pulp.LpStatus[status] == "Optimal":
                result = pulp.value(prob.objective)
                out_buffer.append(str(int(round(result))) if result is not None else "0")
            else:
                out_buffer.append("-1")

        except Exception:
            out_buffer.append("-1")
            if 'prob' in locals(): del prob
            gc.collect()
            continue
            
        # Limpeza manual de memória para evitar Memory Limit Exceeded 
        del coeffs
        del target_wins_vars
        if 'expr_t' in locals(): del expr_t
        gc.collect() # Invoca o Garbage Collector

    # Output final formatado
    sys.stdout.write("\n".join(out_buffer) + "\n")

if __name__ == "__main__":
    solve()