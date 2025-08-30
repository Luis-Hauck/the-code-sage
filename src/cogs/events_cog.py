@bot.event
async def on_thread_create(thread: discord.Thread):
    creator = thread.owner
    if thread.parent_id == 1402409945672060928:
        try:

            print(f'Novo topico criado por {creator}')
            starter_message = await thread.fetch_message(thread.id)
            print(starter_message)
            minha_embed = discord.Embed(
                title='# Post Criado',
                description=f'Enigma;;;............... {starter_message.content}',
                color=discord.Color.from_rgb(88, 55, 250)

            )
            imagem = discord.File(r"D:\Projects\the-code-sage\assets\images\img.png", "img.png")
            minha_embed.set_image(url='attachment://img.png')
            await starter_message.reply(embed=minha_embed, file=imagem)

        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            await thread.send(f'`{creator.name} é preciso colocar uma descrição')



