import discord
from discord.ext import commands
import asyncio,csv,io,requests
from typing import List,Dict,Optional
import re
from collections import defaultdict,Counter
intents=discord.Intents.default()
intents.message_content=True
bot=commands.Bot(command_prefix='!',intents=intents,help_command=None)
SHEET_URL='https://docs.google.com/spreadsheets/d/1r-5WoC6DcaCk9zJAz2Ct9b531AgoOIpvc98xm8oGg4w/export?format=csv&gid=741413211'
class BlockTanksData:
	def __init__(self):self.matches=[];self.players=set()
	async def load_data(self):
		'Load data from Google Sheets'
		try:
			response=requests.get(SHEET_URL);response.raise_for_status();csv_reader=csv.DictReader(io.StringIO(response.text));self.matches=[];self.players=set()
			for row in csv_reader:
				if row.get('Winner/P1')and row.get('Winner/P1')!='Winner/P1':
					match={'winner':row.get('Winner/P1','').strip(),'loser':row.get('Loser/P2','').strip(),'result':row.get('Result','').strip(),'map':row.get('Map','').strip(),'region':row.get('Region','').strip(),'winner_kills':self.safe_int(row.get('Winner Kills','0')),'loser_kills':self.safe_int(row.get('Loser Kills','0')),'winner_kdr':self.safe_float(row.get('Winner KDR','0')),'loser_kdr':self.safe_float(row.get('Loser KDR','0')),'outcome':row.get('Outcome','').strip(),'winner_points':self.safe_float(row.get('Winner Points','0')),'loser_points':self.safe_float(row.get('Loser Points','0'))};self.matches.append(match)
					if match['winner']and match['winner']!='[RESIGNED]':self.players.add(match['winner'])
					if match['loser']and match['loser']!='[RESIGNED]':self.players.add(match['loser'])
			print(f"Loaded {len(self.matches)} matches and {len(self.players)} players");return True
		except Exception as e:print(f"Error loading data: {e}");return False
	def safe_int(self,value):
		try:return int(float(value))if value else 0
		except:return 0
	def safe_float(self,value):
		try:return float(value)if value else .0
		except:return .0
game_data=BlockTanksData()
@bot.event
async def on_ready():print(f"{bot.user} has connected to Discord!");await game_data.load_data();print('Data loaded successfully!')
@bot.command(name='refresh')
async def refresh_data(ctx):
	'Refresh data from the spreadsheet';await ctx.send('🔄 Refreshing data from spreadsheet...');success=await game_data.load_data()
	if success:await ctx.send(f"✅ Data refreshed! Loaded {len(game_data.matches)} matches and {len(game_data.players)} players.")
	else:await ctx.send('❌ Failed to refresh data. Please try again later.')
@bot.command(name='player')
async def player_stats(ctx,*,player_name=None):
	'Get stats for a specific player'
	if not player_name:await ctx.send('Please provide a player name: `!player PlayerName`');return
	found_player=None
	for p in game_data.players:
		if p.lower()==player_name.lower():found_player=p;break
	if not found_player:similar=[p for p in game_data.players if player_name.lower()in p.lower()];suggestion_text=f"\nDid you mean: {", ".join(similar[:5])}"if similar else'';await ctx.send(f"Player '{player_name}' not found.{suggestion_text}");return
	wins=0;losses=0;draws=0;total_kills=0;total_deaths=0;total_points=.0;maps_played=Counter();regions_played=Counter()
	for match in game_data.matches:
		if match['winner']==found_player:
			if match['outcome']=='Draw':draws+=1;total_points+=match['winner_points']
			else:wins+=1;total_points+=match['winner_points']
			total_kills+=match['winner_kills'];total_deaths+=match['loser_kills'];maps_played[match['map']]+=1;regions_played[match['region']]+=1
		elif match['loser']==found_player:
			if match['outcome']=='Draw':draws+=1;total_points+=match['loser_points']
			else:losses+=1;total_points+=match['loser_points']
			total_kills+=match['loser_kills'];total_deaths+=match['winner_kills'];maps_played[match['map']]+=1;regions_played[match['region']]+=1
	total_games=wins+losses+draws;kdr=total_kills/max(total_deaths,1);embed=discord.Embed(title=f"📊 Stats for {found_player}",color=65280);win_rate=wins/max(total_games,1)*100;embed.add_field(name='🏆 Record',value=f"**{wins}W - {losses}L - {draws}D**\nWin Rate: {win_rate:.1f}%",inline=True);embed.add_field(name='⚔️ Combat',value=f"**{total_kills}** kills\n**{total_deaths}** deaths\n**{kdr:.2f}** K/D",inline=True);embed.add_field(name='📈 Points',value=f"**{total_points:.1f}** total",inline=True)
	if maps_played:fav_map=maps_played.most_common(1)[0];embed.add_field(name='🗺️ Favorite Map',value=f"{fav_map[0]} ({fav_map[1]} games)",inline=True)
	if regions_played:main_region=regions_played.most_common(1)[0];embed.add_field(name='🌍 Main Region',value=f"{main_region[0]} ({main_region[1]} games)",inline=True)
	embed.add_field(name='🎮 Total Games',value=str(total_games),inline=True);await ctx.send(embed=embed)
@bot.command(name='leaderboard',aliases=['lb','top'])
async def leaderboard(ctx,stat='points'):
	'Show leaderboard by wins, points, kdr, or kills';valid_stats=['wins','points','kdr','kills','games']
	if stat.lower()not in valid_stats:await ctx.send(f"Invalid stat. Choose from: {", ".join(valid_stats)}");return
	player_stats={}
	for player in game_data.players:
		wins=losses=draws=kills=deaths=0;points=.0
		for match in game_data.matches:
			if match['winner']==player:
				if match['outcome']=='Draw':draws+=1
				else:wins+=1
				points+=match['winner_points'];kills+=match['winner_kills'];deaths+=match['loser_kills']
			elif match['loser']==player:
				if match['outcome']=='Draw':draws+=1
				else:losses+=1
				points+=match['loser_points'];kills+=match['loser_kills'];deaths+=match['winner_kills']
		total_games=wins+losses+draws;kdr=kills/max(deaths,1);player_stats[player]={'wins':wins,'points':points,'kdr':kdr,'kills':kills,'games':total_games}
	stat_lower=stat.lower();sorted_players=sorted(player_stats.items(),key=lambda x:x[1][stat_lower],reverse=True);stat_names={'wins':'🏆 Wins Leaderboard','points':'📈 Points Leaderboard','kdr':'⚔️ K/D Ratio Leaderboard','kills':'💀 Kills Leaderboard','games':'🎮 Games Played Leaderboard'};embed=discord.Embed(title=stat_names[stat_lower],color=16766720);leaderboard_text=''
	for(i,(player,stats))in enumerate(sorted_players[:22],1):
		medal='🥇'if i==1 else'🥈'if i==2 else'🥉'if i==3 else f"{i}."
		if stat_lower=='points':value=f"{stats[stat_lower]:.1f}"
		elif stat_lower=='kdr':value=f"{stats[stat_lower]:.2f}"
		else:value=str(int(stats[stat_lower]))
		leaderboard_text+=f"{medal} **{player}** - {value}\n"
	embed.description=leaderboard_text;await ctx.send(embed=embed)
@bot.command(name='match')
async def recent_matches(ctx,*,player_name=None):
	'Show recent matches for a player or overall';matches_to_show=game_data.matches[-10:]
	if player_name:
		found_player=None
		for p in game_data.players:
			if p.lower()==player_name.lower():found_player=p;break
		if not found_player:await ctx.send(f"Player '{player_name}' not found.");return
		player_matches=[]
		for match in game_data.matches:
			if match['winner']==found_player or match['loser']==found_player:player_matches.append(match)
		matches_to_show=player_matches[-10:];embed_title=f"📝 Recent matches for {found_player}"
	else:embed_title='📝 Recent matches'
	embed=discord.Embed(title=embed_title,color=39423);match_text=''
	for match in reversed(matches_to_show):
		result=match['result'];map_name=match['map'];region=match['region']
		if match['outcome']=='Draw':match_text+=f"🤝 **{match["winner"]}** vs **{match["loser"]}** - {result} on {map_name} ({region})\n"
		else:match_text+=f"🏆 **{match["winner"]}** beat **{match["loser"]}** - {result} on {map_name} ({region})\n"
	if not match_text:match_text='No matches found.'
	embed.description=match_text;await ctx.send(embed=embed)
@bot.command(name='map')
async def map_stats(ctx,*,map_name=None):
	'Show statistics for a specific map or list all maps'
	if not map_name:
		maps=Counter()
		for match in game_data.matches:
			if match['map']:maps[match['map']]+=1
		embed=discord.Embed(title='🗺️ Available Maps',color=65433);map_list=''
		for(map_name,count)in maps.most_common():map_list+=f"**{map_name}** - {count} matches\n"
		embed.description=map_list;await ctx.send(embed=embed);return
	map_matches=[m for m in game_data.matches if m['map'].lower()==map_name.lower()]
	if not map_matches:await ctx.send(f"No matches found on map '{map_name}'");return
	total_matches=len(map_matches);total_kills=sum(m['winner_kills']+m['loser_kills']for m in map_matches);avg_kills=total_kills/total_matches;regions=Counter(m['region']for m in map_matches);players=Counter()
	for match in map_matches:
		if match['winner']!='[RESIGNED]':players[match['winner']]+=1
		if match['loser']!='[RESIGNED]':players[match['loser']]+=1
	actual_map_name=map_matches[0]['map'];embed=discord.Embed(title=f"🗺️ {actual_map_name} Statistics",color=65433);embed.add_field(name='📊 Total Matches',value=str(total_matches),inline=True);embed.add_field(name='💀 Avg Kills/Game',value=f"{avg_kills:.1f}",inline=True);embed.add_field(name='🌍 Top Region',value=regions.most_common(1)[0][0],inline=True)
	if players:top_player=players.most_common(1)[0];embed.add_field(name='👑 Most Active Player',value=f"{top_player[0]} ({top_player[1]} games)",inline=False)
	await ctx.send(embed=embed)
@bot.command(name='vs')
async def head_to_head(ctx,player1,*,player2):
	'Compare two players head-to-head';found_p1=found_p2=None
	for p in game_data.players:
		if p.lower()==player1.lower():found_p1=p
		if p.lower()==player2.lower():found_p2=p
	if not found_p1:await ctx.send(f"Player '{player1}' not found.");return
	if not found_p2:await ctx.send(f"Player '{player2}' not found.");return
	h2h_matches=[]
	for match in game_data.matches:
		if match['winner']==found_p1 and match['loser']==found_p2 or match['winner']==found_p2 and match['loser']==found_p1:h2h_matches.append(match)
	if not h2h_matches:await ctx.send(f"No matches found between {found_p1} and {found_p2}");return
	p1_wins=p1_kills=p1_deaths=0;p2_wins=p2_kills=p2_deaths=0;draws=0
	for match in h2h_matches:
		if match['outcome']=='Draw':draws+=1
		elif match['winner']==found_p1:p1_wins+=1
		else:p2_wins+=1
		if match['winner']==found_p1:p1_kills+=match['winner_kills'];p1_deaths+=match['loser_kills'];p2_kills+=match['loser_kills'];p2_deaths+=match['winner_kills']
		else:p2_kills+=match['winner_kills'];p2_deaths+=match['loser_kills'];p1_kills+=match['loser_kills'];p1_deaths+=match['winner_kills']
	embed=discord.Embed(title=f"⚔️ {found_p1} vs {found_p2}",color=16739179);embed.add_field(name='🏆 Head-to-Head Record',value=f"**{found_p1}**: {p1_wins}W\n**{found_p2}**: {p2_wins}W\n**Draws**: {draws}",inline=True);p1_kdr=p1_kills/max(p1_deaths,1);p2_kdr=p2_kills/max(p2_deaths,1);embed.add_field(name='💀 Combat Stats',value=f"**{found_p1}**: {p1_kills}K/{p1_deaths}D ({p1_kdr:.2f})\n"+f"**{found_p2}**: {p2_kills}K/{p2_deaths}D ({p2_kdr:.2f})",inline=True);embed.add_field(name='🎮 Total Matches',value=str(len(h2h_matches)),inline=True);await ctx.send(embed=embed)
@bot.command(name='help')
async def help_command(ctx):'Show available commands';embed=discord.Embed(title='🤖 BlockTanks League Bot Commands',color=7506394);commands_text='\n    `!player <name>` - Get detailed stats for a player\n    `!leaderboard [stat]` - Show leaderboard (wins/points/kdr/kills/games)\n    `!match [player]` - Show recent matches (overall or for a player)\n    `!map [name]` - Show map statistics or list all maps\n    `!vs <player1> <player2>` - Head-to-head comparison\n    `!refresh` - Refresh data from spreadsheet\n    `!help` - Show this help message\n    ';embed.description=commands_text;embed.add_field(name='Examples:',value='`!player Giant_Professor`\n`!leaderboard points`\n`!vs blu NYS_Lask`',inline=False);await ctx.send(embed=embed)
if __name__=='__main__':bot.run(os.getenv("DISCORD_TOKEN"))
