from pokedex import pokedex as dex

from userbot.events import register, grp_exclude

@register(outgoing=True, pattern="pokedex")
@grp_exclude()
async def pokedex(dexter):
    pokedex = dex.Pokedex(version = 'v1')
    pokemon_name = str(dexter.text[9: ])
    pokemon = pokedex.get_pokemon_by_name(pokemon_name)
    pokedetails = str(pokemon)
    
  #================= POKEMON STATS ================= #   
    Name = pokedetails[2]                            #
    Species = pokedetails[3]                         #
    Type = pokedetails[4]                            #
    Ability = pokedetails[5]                         #                   
    EggGroup = pokedetails[6]                        #
    Stage = pokedetails[10]                          #
    #Evolution = pokedetails[10]                      #
    Gender = pokedetails[7]                          #
    Height = pokedetails[8]                          #
    Weight = pokedetails[9]                          #
    Sprite = pokedetails[18]                         #
    Description = pokedetails[19]                    #
  #================================================= #
  
    message = (
        f"**Name: **{Name}"
        f"**Type: **{Type}"
        f"**Abilities: **{Ability}"
        f"**Gender: **{Gender}"
        f"**Height: **{Height}"
        f"**Weight: **{Weight}"
        f"**Stage: **{Stage}"
        #f"**Evolution: **{Evolution}"
        f"**EggGroup: **{EggGroup}"
        f"**Description: **__{Description}__"
    )
    
    await dexter.reply(message)
