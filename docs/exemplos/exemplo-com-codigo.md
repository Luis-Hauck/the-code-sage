# Exemplo curto com código — Documentando o comando /perfil

Este é um exemplo mínimo de documentação com um trecho de código real do projeto.

Nota: este arquivo é um EXEMPLO de como documentar um comando. Para criar novas docs de comandos, use o MODELO em `docs/modelos/comando.md`.

Objetivo: mostrar como descrever rapidamente um comando (ação) e referenciar o pedaço de código correspondente.

## Resumo
- Nome do comando: `/perfil`
- Cog/Arquivo: `src/cogs/user_cog.py`
- Para quem é: Usuário final que quer ver seu progresso e saldo.
- Resultado: Retorna um Embed com nível, XP, progresso e moedas, além do item equipado.

## Parâmetros
- Não possui parâmetros (usa o usuário da interação atual).

## Comportamento
- Defer da resposta como ephemeral (visível só ao usuário).
- Busca dados do perfil no `UserService`.
- Monta um Embed e envia no followup.

## Trecho de código essencial

```python
# src/cogs/user_cog.py — método resumido
@app_commands.command(name="perfil", description="Exibe o seu perfil.")
async def view_profile(self, interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    user_id = interaction.user.id
    guild = interaction.guild

    profile_data = await self.user_service.get_user_profile(user_id, guild)
    if not profile_data:
        await interaction.followup.send(
            embed=create_error_embed("Erro", "Perfil não encontrado."), ephemeral=True
        )
        return

    profile_embed = UserEmbeds.view_profile(
        user_name=profile_data['username'],
        current_level=profile_data['current_level'],
        current_xp=profile_data['current_xp'],
        xp_next_level=profile_data['xp_next_level'],
        progress_percent=profile_data['progress_percent'],
        coin_balance=profile_data['coin_balance'],
        equipped_item_name=profile_data['equipped_item_name']
    )

    await interaction.followup.send(embed=profile_embed)
```

Dica: Ao documentar, você não precisa colar o método inteiro. Traga apenas o miolo que ajuda a explicar o fluxo.

## Erros e mensagens
- "Perfil não encontrado." — Quando o serviço não retorna dados para o usuário.

## Relacionados
- Service: `UserService.get_user_profile`
- Embeds: `UserEmbeds.view_profile`

## Próximos passos
- Use este arquivo como referência rápida e, quando for documentar outro comando, copie o modelo em: [../modelos/comando.md](../referencias/comandos/equipar.md).
- Veja também o exemplo introdutório: [primeiros-passos.md](primeiros-passos.md)
