from google.generativeai import generate_text
from rest_framework.response import Response
from django.http import HttpResponse
import google.generativeai as genai

api_key = 'AIzaSyBKVx96_XykSFS7T4Gz_kgfEJj9yrF4BkI'
genai.configure(api_key=api_key)

# Função para gerar o texto
def generate_generative_text(prompt: str) -> str:
    global previous_responses
    
    # Inicializa a lista de respostas anteriores, se ainda não existir
    if 'previous_responses' not in globals():
        previous_responses = []

    while len(previous_responses) < 10:

        # Se não houver respostas anteriores, apenas use o prompt atual
        if len(previous_responses) == 0:
            full_prompt = prompt
        else:
            # Combina as respostas anteriores com o prompt atual
            comparison_prompt = " ".join(["Compare with previous analyses and make sure your analysis is robust."] + previous_responses)
            full_prompt = f"{comparison_prompt} {prompt}"

        # Gera a resposta
        response = generate_text(
            model='models/text-bison-001',  
            prompt=full_prompt,
            temperature=0.2,  
            max_output_tokens=1000
        )
        
        # Avalia a qualidade da resposta usando um critério simples, como o comprimento
        quality_score = len(response.result)

        # Armazena a resposta junto com sua pontuação de qualidade
        previous_responses.append((quality_score, response.result))

    # Quando tivermos 10 ou mais análises, selecionamos a melhor
    best_analysis = max(previous_responses, key=lambda x: x[0])

    # Mantém apenas as 5 melhores análises
    previous_responses = sorted(previous_responses, key=lambda x: x[0], reverse=True)[:5]

    return best_analysis[1]