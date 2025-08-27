from __future__ import annotations
import os
import asyncio
import json
from typing import Literal, TypedDict
import streamlit as st

from agent.agent_pydantic import crm_expert_agent, CRMAgentDeps
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    UserPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    RetryPromptPart,
    ModelMessagesTypeAdapter
)

import clients

# Configuração dos Clients
openai_client = clients.new_client_openai()

supabase = clients.new_supabase_client()

class ChatMessage(TypedDict):
    role: Literal['user', 'model']
    timestamp: str
    content: str

def display_message(part):
    # system-prompt
    if part.part_kind == 'system-prompt':
        with st.chat_message('system'):
            st.markdown(f'**System**: {part.content}')
    # user-prompt
    elif part.part_kind == 'user-prompt':
        with st.chat_message('user'):
            st.markdown(part.content)
    # text
    elif part.part_kind == 'text':
        with st.chat_message('assistant'):
            st.markdown(part.content)

async def run_agent_with_streaming(user_input: str):
    # Inicializar as dependências
    deps = CRMAgentDeps(
        supabase=supabase,
        openai_client=openai_client
    )

    # Executa agent em stream
    async with crm_expert_agent.run_stream(
        user_input,
        deps=deps,
        message_history=st.session_state.messages[:-1]
    ) as result:
        partial_text = ''
        message_placeholder = st.empty()

        # Renderiza o texto conforme ele chega
        async for chunk in result.stream_text(delta=True):
            partial_text += chunk
            message_placeholder.markdown(partial_text)

        # Filtra as mensagens e adiciona no histórico da sessão
        filtered_messages = [msg for msg in result.new_messages()
                             if not (hasattr(msg, 'parts') and
                                     any(part.part_kind == 'user-prompt' for part in msg.parts))]
        
        st.session_state.messages.extend(filtered_messages)

async def main():
    st.title('CRM Agentic RAG')
    st.write('Faça perguntas sobre os relatórios do CRM.')

    # Inicializa o histórico de mensagens caso ele não exista
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    for msg in st.session_state.messages:
        if isinstance(msg, ModelRequest) or isinstance(msg, ModelResponse):
            for part in msg.parts:
                display_message(part=part)
    
    user_input = st.chat_input("Faça sua pergunta aqui...")

    if user_input:
        st.session_state.messages.append(
            ModelRequest(parts=[UserPromptPart(content=user_input)])
        )

        with st.chat_message('user'):
            st.markdown(user_input)
        
        with st.chat_message('assistant'):
            await run_agent_with_streaming(user_input=user_input)

if __name__ == '__main__':
    asyncio.run(main=main())