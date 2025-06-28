import discord
from discord.ext import commands,tasks
from discord.ui import Button,View
import asyncio,csv,io,requests
from typing import List,Dict,Optional
import re
from collections import defaultdict,Counter
from datetime import datetime
import statistics
import os
import math
intents=discord.Intents.default()
intents.message_content=True
bot=commands.Bot(command_prefix='!',intents=intents,help_command=None)
SHEET_URL='https://docs.google.com/spreadsheets/d/1r-5WoC6DcaCk9zJAz2Ct9b531AgoOIpvc98xm8oGg4w/export?format=csv&gid=741413211'
HALL_OF_FAME_URL='https://docs.google.com/spreadsheets/d/1r-5WoC6DcaCk9zJAz2Ct9b531AgoOIpvc98xm8oGg4w/export?format=csv&gid=0'
class BlockTanksData:
	def __init__(self):self.matches=[];self.players=set();self.last_updated=None;self.hall_of_fame=[]
	async def load_data(self):
		try:
			response=requests.get(SHEET_URL,timeout=30);response.raise_for_status();csv_reader=csv.DictReader(io.StringIO(response.text));self.matches=[];self.players=set()
			for row in csv_reader:
				if row.get('Winner/P1')and row.get('Winner/P1')!='Winner/P1':
					match={'winner':row.get('Winner/P1','').strip(),'loser':row.get('Loser/P2','').strip(),'result':row.get('Result','').strip(),'map':row.get('Map','').strip(),'region':row.get('Region','').strip(),'winner_kills':self.safe_int(row.get('Winner Kills','0')),'loser_kills':self.safe_int(row.get('Loser Kills','0')),'winner_kdr':self.safe_float(row.get('Winner KDR','0')),'loser_kdr':self.safe_float(row.get('Loser KDR','0')),'outcome':row.get('Outcome','').strip(),'winner_points':self.safe_float(row.get('Winner Points','0')),'loser_points':self.safe_float(row.get('Loser Points','0')),'date':row.get('Date','').strip(),'time':row.get('Time','').strip(),'tournament':row.get('Tournament','').strip(),'week':row.get('Week','').strip(),'season':row.get('Season','').strip()};self.matches.append(match)
					if match['winner']and match['winner']!='[RESIGNED]':self.players.add(match['winner'])
					if match['loser']and match['loser']!='[RESIGNED]':self.players.add(match['loser'])
			hof_response=requests.get(HALL_OF_FAME_URL,timeout=30);hof_response.raise_for_status();hof_data=[];lines=hof_response.text.strip().split('\n')
			if len(lines)>1:
				for(i,line)in enumerate(lines[1:],2):
					parts=line.split(',')
					if len(parts)>=10 and parts[1].strip():
						player_name=parts[1].strip()
						if player_name and player_name!='Player':hof_data.append({'position':i-1,'player':player_name,'matches':self.safe_int(parts[2]),'wins':self.safe_int(parts[3]),'draws':self.safe_int(parts[4]),'losses':self.safe_int(parts[5]),'kills':self.safe_int(parts[6]),'deaths':self.safe_int(parts[7]),'kdr':self.safe_float(parts[8]),'points':self.safe_float(parts[9]),'winrate':round(self.safe_int(parts[3])/max(self.safe_int(parts[2]),1)*100,2),'tier':self.get_tier(self.safe_float(parts[9]),self.safe_int(parts[3]))})
			self.hall_of_fame=hof_data;self.last_updated=datetime.now();print(f"Loaded {len(self.matches)} matches, {len(self.players)} players, {len(self.hall_of_fame)} HOF entries");return True
		except Exception as e:print(f"Error loading data: {e}");return False
	def safe_int(self,value):
		try:return int(float(str(value).strip()))if value else 0
		except:return 0
	def safe_float(self,value):
		try:return float(str(value).strip())if value else .0
		except:return .0
	def get_tier(self,points,wins):
		if points>=2000 and wins>=25:return'Diamond'
		elif points>=1000 and wins>=15:return'Platinum'
		elif points>=500 and wins>=10:return'Gold'
		elif points>=100 and wins>=5:return'Silver'
		elif points>=0:return'Bronze'
		else:return'Unranked'
game_data=BlockTanksData()
class PaginatorView(View):
	def __init__(self,ctx,pages,timeout=60):super().__init__(timeout=timeout);self.ctx=ctx;self.pages=pages;self.current_page=0;self.message=None
	async def show_page(self,page_num):
		self.current_page=page_num%len(self.pages);page=self.pages[self.current_page];self.first_page.disabled=self.current_page==0;self.prev_page.disabled=self.current_page==0;self.next_page.disabled=self.current_page==len(self.pages)-1;self.last_page.disabled=self.current_page==len(self.pages)-1;page_counter=f"Page {self.current_page+1}/{len(self.pages)}"
		if isinstance(page,discord.Embed):
			if not page.footer.text:page.set_footer(text=page_counter)
			else:page.set_footer(text=f"{page.footer.text} • {page_counter}")
			await self.message.edit(embed=page,view=self)
		else:await self.message.edit(content=f"{page}\n\n{page_counter}",view=self)
	@discord.ui.button(emoji='⏮️',style=discord.ButtonStyle.secondary)
	async def first_page(self,interaction,button):await interaction.response.defer();await self.show_page(0)
	@discord.ui.button(emoji='◀️',style=discord.ButtonStyle.primary)
	async def prev_page(self,interaction,button):await interaction.response.defer();await self.show_page(self.current_page-1)
	@discord.ui.button(emoji='▶️',style=discord.ButtonStyle.primary)
	async def next_page(self,interaction,button):await interaction.response.defer();await self.show_page(self.current_page+1)
	@discord.ui.button(emoji='⏭️',style=discord.ButtonStyle.secondary)
	async def last_page(self,interaction,button):await interaction.response.defer();await self.show_page(len(self.pages)-1)
	async def interaction_check(self,interaction):
		if interaction.user!=self.ctx.author:await interaction.response.send_message("You can't control this pagination!",ephemeral=True);return False
		return True
	async def on_timeout(self):
		for item in self.children:item.disabled=True
		try:await self.message.edit(view=self)
		except:pass
@bot.event
async def on_ready():print(f"{bot.user} has connected to Discord!");await game_data.load_data();auto_refresh_data.start();print('Data loaded successfully!')
@tasks.loop(minutes=5)
async def auto_refresh_data():success=await game_data.load_data();print(f"{"✅"if success else"❌"} Auto-refresh at {datetime.now()}")
@bot.command(name='refresh')
async def refresh_data(ctx):
	await ctx.send('🔄 Refreshing data...');success=await game_data.load_data()
	if success:await ctx.send(f"✅ Loaded {len(game_data.matches)} matches, {len(game_data.players)} players, {len(game_data.hall_of_fame)} HOF entries")
	else:await ctx.send('❌ Failed to refresh data')
@bot.command(name='hof',aliases=['halloffame','rankings'])
async def hall_of_fame(ctx,*,tier_filter=None):
	if not game_data.hall_of_fame:await ctx.send('Hall of Fame data not loaded');return
	filtered_hof=game_data.hall_of_fame
	if tier_filter:
		filtered_hof=[entry for entry in game_data.hall_of_fame if tier_filter.lower()in entry['tier'].lower()]
		if not filtered_hof:await ctx.send(f"No entries for tier '{tier_filter}'");return
	entries_per_page=15;pages=[];tier_emojis={'Diamond':'💎','Platinum':'🔶','Gold':'⭐','Silver':'🔹','Bronze':'🔸','Unranked':'❌'}
	for i in range(0,len(filtered_hof),entries_per_page):
		page_entries=filtered_hof[i:i+entries_per_page];embed=discord.Embed(title=f"🏆 BTEL Hall of Fame"+(f" - {tier_filter}"if tier_filter else''),color=16766720)
		for entry in page_entries:tier_emoji=tier_emojis.get(entry['tier'],'🏅');value=f"**#{entry["position"]} | {entry["tier"]}** {tier_emoji}\n**W-D-L:** {entry["wins"]}-{entry["draws"]}-{entry["losses"]} ({entry["winrate"]:.1f}%)\n**K/D:** {entry["kdr"]:.2f} ({entry["kills"]}/{entry["deaths"]})\n**Points:** {entry["points"]:.0f} | **Games:** {entry["matches"]}";embed.add_field(name=f"{entry["player"]}",value=value,inline=True)
		embed.set_footer(text=f"Total Players: {len(filtered_hof)}");pages.append(embed)
	if not pages:await ctx.send('No Hall of Fame entries found');return
	view=PaginatorView(ctx,pages);view.message=await ctx.send(embed=pages[0],view=view)
@bot.command(name='player',aliases=['p','stats'])
async def player_stats(ctx,*,player_name=None):
	if not player_name:await ctx.send('Please specify a player name');return
	player_matches=[m for m in game_data.matches if player_name.lower()in m['winner'].lower()or player_name.lower()in m['loser'].lower()];exact_match=next((p for p in game_data.players if p.lower()==player_name.lower()),None)
	if not exact_match and player_matches:possible=list(set([m['winner']for m in player_matches]+[m['loser']for m in player_matches]));await ctx.send(f"Player not found. Did you mean: {", ".join(possible[:5])}");return
	player=exact_match;hof_entry=next((h for h in game_data.hall_of_fame if h['player'].lower()==player.lower()),None)
	if hof_entry:
		tier_emojis={'Diamond':'💎','Platinum':'🔶','Gold':'⭐','Silver':'🔹','Bronze':'🔸','Unranked':'❌'};embed=discord.Embed(title=f"📊 {player} - Player Stats",color=65280);embed.add_field(name='🏆 Ranking',value=f"**#{hof_entry["position"]}** | {hof_entry["tier"]} {tier_emojis.get(hof_entry["tier"],"🏅")}",inline=True);embed.add_field(name='📈 Record',value=f"{hof_entry["wins"]}W-{hof_entry["draws"]}D-{hof_entry["losses"]}L\n({hof_entry["winrate"]:.1f}% WR)",inline=True);embed.add_field(name='⚔️ Combat',value=f"K/D: {hof_entry["kdr"]:.2f}\n{hof_entry["kills"]}K/{hof_entry["deaths"]}D",inline=True);embed.add_field(name='🎮 Performance',value=f"Points: {hof_entry["points"]:.0f}\nGames: {hof_entry["matches"]}",inline=True);embed.add_field(name='📊 Averages',value=f"PPG: {hof_entry["points"]/max(hof_entry["matches"],1):.1f}\nKPG: {hof_entry["kills"]/max(hof_entry["matches"],1):.1f}",inline=True);recent_matches=[m for m in game_data.matches if m['winner']==player or m['loser']==player][-5:]
		if recent_matches:
			recent_text=''
			for match in recent_matches:result='W'if match['winner']==player else'L';opponent=match['loser']if match['winner']==player else match['winner'];recent_text+=f"{result} vs {opponent} | "
			embed.add_field(name='🔄 Recent (Last 5)',value=recent_text[:-3],inline=False)
		await ctx.send(embed=embed)
	else:await ctx.send(f"No Hall of Fame data found for {player}")
@bot.command(name='leaderboard',aliases=['lb','top'])
async def leaderboard(ctx,stat='points',season=None):
	valid_stats=['wins','points','kdr','kills','games','winrate','ppg','kpg','position']
	if stat.lower()not in valid_stats:await ctx.send(f"Invalid stat. Choose: {", ".join(valid_stats)}");return
	if stat.lower()=='position':sorted_hof=sorted(game_data.hall_of_fame,key=lambda x:x['position'])
	else:sorted_hof=sorted(game_data.hall_of_fame,key=lambda x:x.get(stat.lower(),0),reverse=True)
	stat_names={'wins':'🏆 Wins','points':'📈 Points','kdr':'⚔️ K/D Ratio','kills':'💀 Kills','games':'🎮 Games','winrate':'📊 Win Rate','ppg':'📈 PPG','kpg':'⚔️ KPG','position':'🏆 Rankings'};entries_per_page=15;pages=[]
	for i in range(0,len(sorted_hof),entries_per_page):
		page_entries=sorted_hof[i:i+entries_per_page];embed=discord.Embed(title=f"{stat_names.get(stat.lower(),stat)} Leaderboard",color=16753920);leaderboard_text=''
		for(j,entry)in enumerate(page_entries,start=i+1):
			medal='🥇'if j==1 else'🥈'if j==2 else'🥉'if j==3 else f"{j}."
			if stat.lower()in['points','ppg','kpg']:value=f"{entry.get(stat.lower(),0):.1f}"
			elif stat.lower()in['kdr','winrate']:
				value=f"{entry.get(stat.lower(),0):.2f}"
				if stat.lower()=='winrate':value+='%'
			elif stat.lower()=='position':value=f"#{entry["position"]}"
			else:value=str(entry.get(stat.lower(),0))
			leaderboard_text+=f"{medal} **{entry["player"]}** - {value} ({entry["matches"]} games)\n"
		embed.description=leaderboard_text;embed.set_footer(text=f"Total players: {len(sorted_hof)}");pages.append(embed)
	if not pages:await ctx.send('No leaderboard data available');return
	view=PaginatorView(ctx,pages);view.message=await ctx.send(embed=pages[0],view=view)
@bot.command(name='vs',aliases=['versus','h2h'])
async def head_to_head(ctx,player1,player2):
	matches=[m for m in game_data.matches if m['winner'].lower()==player1.lower()and m['loser'].lower()==player2.lower()or m['winner'].lower()==player2.lower()and m['loser'].lower()==player1.lower()]
	if not matches:await ctx.send(f"No matches found between {player1} and {player2}");return
	p1_wins=len([m for m in matches if m['winner'].lower()==player1.lower()]);p2_wins=len([m for m in matches if m['winner'].lower()==player2.lower()]);embed=discord.Embed(title=f"⚔️ {player1} vs {player2}",color=16739179);embed.add_field(name='📊 Head-to-Head',value=f"{player1}: {p1_wins} wins\n{player2}: {p2_wins} wins",inline=False)
	if len(matches)<=10:
		recent_text=''
		for match in matches[-10:]:winner='**'+match['winner']+'**'if match['winner'].lower()==player1.lower()else match['winner'];loser='**'+match['loser']+'**'if match['loser'].lower()==player1.lower()else match['loser'];recent_text+=f"{winner} def. {loser} ({match["winner_kills"]}-{match["loser_kills"]})\n"
		embed.add_field(name='🎮 Match History',value=recent_text,inline=False)
	await ctx.send(embed=embed)
@bot.command(name='compare',aliases=['comp'])
async def compare_players(ctx,player1,player2):
	hof1=next((h for h in game_data.hall_of_fame if h['player'].lower()==player1.lower()),None);hof2=next((h for h in game_data.hall_of_fame if h['player'].lower()==player2.lower()),None)
	if not hof1 or not hof2:await ctx.send('One or both players not found in Hall of Fame');return
	embed=discord.Embed(title=f"📊 {player1} vs {player2} Comparison",color=10181046);stats=[('Position','position',lambda x:f"#{x}"),('Wins','wins',str),('Win Rate','winrate',lambda x:f"{x:.1f}%"),('K/D Ratio','kdr',lambda x:f"{x:.2f}"),('Points','points',lambda x:f"{x:.0f}"),('Games','matches',str)]
	for(stat_name,stat_key,formatter)in stats:
		val1,val2=hof1[stat_key],hof2[stat_key]
		if stat_key=='position':better=player1 if val1<val2 else player2 if val2<val1 else'Tie'
		else:better=player1 if val1>val2 else player2 if val2>val1 else'Tie'
		embed.add_field(name=f"{stat_name}",value=f"{player1}: {formatter(val1)}\n{player2}: {formatter(val2)}\n**Edge: {better}**",inline=True)
	await ctx.send(embed=embed)
@bot.command(name='help')
async def help_command(ctx):
	pages=[];main_embed=discord.Embed(title='🤖 BTEL Bot Commands',color=5793266);main_embed.description='Navigate through pages to see all commands';pages.append(main_embed);commands_data=[('Player Commands',[('`!player <name>`','Detailed player statistics'),('`!compare <p1> <p2>`','Compare two players'),('`!vs <p1> <p2>`','Head-to-head matchup')]),('Leaderboards',[('`!hof [tier]`','Hall of Fame rankings'),('`!leaderboard [stat]`','Various stat leaderboards'),('`!lb wins/points/kdr/kills`','Specific leaderboards')]),('System',[('`!refresh`','Refresh data'),('`!help`','Show this help')])]
	for(category,cmds)in commands_data:
		embed=discord.Embed(title=f"📚 {category}",color=5793266)
		for(cmd,desc)in cmds:embed.add_field(name=cmd,value=desc,inline=False)
		pages.append(embed)
	view=PaginatorView(ctx,pages);view.message=await ctx.send(embed=pages[0],view=view)
if __name__=='__main__':bot.run(os.getenv('DISCORD_TOKEN'))
