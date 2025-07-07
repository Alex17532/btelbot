A7='loser_points'
A6='outcome'
A5=isinstance
A1='❌ No tournament data available. Use `!refresh` to load data.'
A0='best_unbeaten'
z='best_win'
y='current'
x='holder'
w='value'
v='winner_points'
u='last_updated'
t=enumerate
s=reversed
q='❌ No match data available. Use `!refresh` to load data.'
p='draws'
o='losses'
n='result'
m=float
l=Exception
k='total_kills'
j='total_matches'
i='kd_ratio'
h=None
e=False
d='streaks'
c='regions'
b='maps'
a='region'
Z='loser'
Y=sorted
X=max
W=len
V='map'
U='winner'
T='last_matches'
S='loser_kills'
R='winner_kills'
Q='records'
P='opponents'
O='wins'
N=''
M='d'
L='l'
K='points'
J='deaths'
H=print
I='w'
G='players'
C=True
F='kills'
B='matches'
import discord as E
from discord.ext import commands as r
import asyncio,aiohttp,re,os
from datetime import datetime as A8
from typing import Dict,List,Optional,Tuple
import json
from collections import defaultdict as f
import statistics
A2=E.Intents.default()
D.remove_command('help')
A2.message_content=C
D=r.Bot(command_prefix='!',intents=A2)
A3={B:'https://docs.google.com/spreadsheets/d/19pi4JoomyimkKCFAzDVLYHjai16MiPBM-4y_NgucSKo/edit?gid=741413211#gid=741413211','player_stats':'https://docs.google.com/spreadsheets/d/19pi4JoomyimkKCFAzDVLYHjai16MiPBM-4y_NgucSKo/edit?gid=1821177716#gid=1821177716','head_to_head':'https://docs.google.com/spreadsheets/d/19pi4JoomyimkKCFAzDVLYHjai16MiPBM-4y_NgucSKo/edit?gid=1530295764#gid=1530295764',Q:'https://docs.google.com/spreadsheets/d/19pi4JoomyimkKCFAzDVLYHjai16MiPBM-4y_NgucSKo/edit?gid=2035449345#gid=2035449345'}
A={B:[],G:{},Q:{},u:h}
class A9:
	def __init__(A):A.session=h
	async def fetch_sheet_data(A,url):
		if not A.session:A.session=aiohttp.ClientSession()
		try:
			async with A.session.get(url)as B:
				if B.status==200:return await B.text()
				else:raise l(f"Failed to fetch data: {B.status}")
		except l as C:H(f"Error fetching sheet data: {C}");return N
	def parse_table_data(E,html_content):
		A=[];D=html_content.split('\n')
		for B in D:
			if'|'in B and'---'not in B:
				C=[A.strip()for A in B.split('|')]
				if W(C)>3:A.append(C[1:-1])
		return A[1:]if A else[]
	async def refresh_all_data(D):
		F=.0;E='.';H('🔄 Refreshing tournament data...');G=await D.fetch_sheet_data(A3[B]);I=D.parse_table_data(G);J=await D.fetch_sheet_data(A3[Q]);K=D.parse_table_data(J);A[B]=[]
		for C in I:
			if W(C)>=15:L={U:C[0],Z:C[1],n:C[2],V:C[3],a:C[4],R:int(C[5])if C[5].isdigit()else 0,S:int(C[6])if C[6].isdigit()else 0,'winner_kdr':m(C[7])if C[7].replace(E,N).isdigit()else F,'loser_kdr':m(C[8])if C[8].replace(E,N).isdigit()else F,A6:C[9],v:m(C[10])if C[10].replace(E,N).replace('-',N).isdigit()else F,A7:m(C[11])if C[11].replace(E,N).replace('-',N).isdigit()else F};A[B].append(L)
		A[Q]={}
		for C in K:
			if W(C)>=3:M=C[0];O=C[1];P=C[2];A[Q][M]={w:O,x:P}
		D.calculate_player_stats();A[u]=A8.now();H('✅ Tournament data refreshed successfully!')
	def calculate_player_stats(l):
		k='[RESIGNED]';C=f(lambda:{O:0,o:0,p:0,F:0,J:0,K:0,B:[],b:f(lambda:{I:0,L:0,M:0}),c:f(lambda:{I:0,L:0,M:0}),P:f(lambda:{I:0,L:0,M:0,F:0,J:0}),d:{y:0,z:0,A0:0},T:[]})
		for D in A[B]:
			H=D[U];E=D[Z]
			if H!=k:C[H][O]+=1;C[H][F]+=D[R];C[H][J]+=D[S];C[H][K]+=D[v];C[H][b][D[V]][I]+=1;C[H][c][D[a]][I]+=1;C[H][P][E][I]+=1;C[H][P][E][F]+=D[R];C[H][P][E][J]+=D[S];C[H][B].append(D);C[H][T].append('W')
			if E!=k:
				if D[A6]=='Draw':C[E][p]+=1;C[E][b][D[V]][M]+=1;C[E][c][D[a]][M]+=1;C[E][P][H][M]+=1;C[E][T].append('D')
				else:C[E][o]+=1;C[E][b][D[V]][L]+=1;C[E][c][D[a]][L]+=1;C[E][P][H][L]+=1;C[E][T].append('L')
				C[E][F]+=D[S];C[E][J]+=D[R];C[E][K]+=D[A7];C[E][P][H][F]+=D[S];C[E][P][H][J]+=D[R];C[E][B].append(D)
		for(m,N)in C.items():
			N[T]=N[T][-5:];Y=0;e=0;g=0;Q=0;W=0
			for h in s(N[T]):
				if h=='W':Q+=1;W+=1;Y+=1
				elif h=='D':W+=1;Q=0
				else:Q=0;W=0;Y=0
				e=X(e,Q);g=X(g,W)
			N[d][y]=Y;N[d][z]=e;N[d][A0]=g;N[i]=N[F]/X(N[J],1);N[j]=N[O]+N[o]+N[p]
		A[G]=dict(C)
g=A9()
@D.event
async def AC():H(f"🚀 {D.user} has connected to Discord!");H('📊 Loading tournament data...');await g.refresh_all_data();H('✅ Bot is ready to serve!')
@D.command(name='refresh')
async def AD(ctx):
	C=E.Embed(title='🔄 Refreshing Tournament Data',description='Fetching latest data from Google Sheets...',color=65280);D=await ctx.send(embed=C)
	try:await g.refresh_all_data();C=E.Embed(title='✅ Data Refreshed Successfully',description=f"Tournament data updated at {A[u].strftime("%Y-%m-%d %H:%M:%S")}",color=65280);C.add_field(name='📈 Statistics',value=f"**Matches:** {W(A[B])}\n**Players:** {W(A[G])}\n**Records:** {W(A[Q])}",inline=e);await D.edit(embed=C)
	except l as F:C=E.Embed(title='❌ Refresh Failed',description=f"Error: {str(F)}",color=16711680);await D.edit(embed=C)
@D.command(name='leaderboard',aliases=['lb','rankings'])
async def AE(ctx,sort_by=K):
	P='kd';D=sort_by
	if not A[G]:await ctx.send(A1);return
	R=[K,O,F,P,B]
	if D not in R:D=K
	if D==K:H=Y(A[G].items(),key=lambda x:x[1][K],reverse=C)
	elif D==O:H=Y(A[G].items(),key=lambda x:x[1][O],reverse=C)
	elif D==F:H=Y(A[G].items(),key=lambda x:x[1][F],reverse=C)
	elif D==P:H=Y(A[G].items(),key=lambda x:x[1][i],reverse=C)
	elif D==B:H=Y(A[G].items(),key=lambda x:x[1][j],reverse=C)
	M=E.Embed(title=f"🏆 Tournament Leaderboard - {D.title()}",color=16766720);Q=N
	for(L,(S,I))in t(H[:10],1):
		if D==K:J=f"{I[K]:.1f}"
		elif D==O:J=f"{I[O]}"
		elif D==F:J=f"{I[F]}"
		elif D==P:J=f"{I[i]:.2f}"
		elif D==B:J=f"{I[j]}"
		T='🥇'if L==1 else'🥈'if L==2 else'🥉'if L==3 else f"{L}.";Q+=f"{T} **{S}** - {J}\n"
	M.description=Q;M.set_footer(text=f"Sorted by {D} | Use !leaderboard [points/wins/kills/kd/matches]");await ctx.send(embed=M)
@D.command(name='player',aliases=['stats','profile'])
async def AF(ctx,*,player_name=h):
	R=player_name;P=ctx
	if not R:await P.send('❌ Please provide a player name. Usage: `!player <player_name>`');return
	if not A[G]:await P.send(A1);return
	Q=h
	for V in A[G].keys():
		if V.lower()==R.lower():Q=V;break
	if not Q:await P.send(f"❌ Player '{R}' not found in tournament data.");return
	B=A[G][Q];D=E.Embed(title=f"📊 {Q}'s Tournament Profile",color=43775);D.add_field(name='📈 Overall Statistics',value=f"**Wins:** {B[O]}\n**Losses:** {B[o]}\n**Draws:** {B[p]}\n**Matches:** {B[j]}\n**Points:** {B[K]:.1f}",inline=C);D.add_field(name='⚔️ Combat Stats',value=f"**Kills:** {B[F]}\n**Deaths:** {B[J]}\n**K/D Ratio:** {B[i]:.2f}\n**Avg K/Match:** {B[F]/X(B[j],1):.1f}\n**Avg D/Match:** {B[J]/X(B[j],1):.1f}",inline=C);D.add_field(name='🔥 Streaks',value=f"**Current:** {B[d][y]}\n**Best Win:** {B[d][z]}\n**Best Unbeaten:** {B[d][A0]}",inline=C);Z=' - '.join(B[T][-5:])if B[T]else'No recent matches';D.add_field(name='📅 Last 5 Matches',value=f"`{Z}`",inline=e)
	if B[b]:
		a=Y(B[b].items(),key=lambda x:x[1][I],reverse=C)[:3];W=N
		for(f,S)in a:W+=f"**{f}:** {S[I]}W-{S[L]}L-{S[M]}D\n"
		D.add_field(name='🗺️ Top Maps',value=W,inline=C)
	if B[c]:
		U=N
		for(g,H)in B[c].items():
			if H[I]+H[L]+H[M]>0:U+=f"**{g}:** {H[I]}W-{H[L]}L-{H[M]}D\n"
		if U:D.add_field(name='🌍 Regional Performance',value=U,inline=C)
	await P.send(embed=D)
@D.command(name='h2h',aliases=['headtohead','vs'])
async def AG(ctx,player1,player2):
	d=player2;c=player1;W=ctx
	if not A[G]:await W.send(A1);return
	D=h;H=h
	for X in A[G].keys():
		if X.lower()==c.lower():D=X
		elif X.lower()==d.lower():H=X
	if not D:await W.send(f"❌ Player '{c}' not found.");return
	if not H:await W.send(f"❌ Player '{d}' not found.");return
	Y=A[G][D];a=A[G][H];S=E.Embed(title=f"⚔️ {D} vs {H}",color=16739125);R=Y[P].get(H,{I:0,L:0,M:0,F:0,J:0});b=a[P].get(D,{I:0,L:0,M:0,F:0,J:0});S.add_field(name='📊 Head-to-Head Record',value=f"**{D}:** {R[I]}W-{R[L]}L-{R[M]}D\n**{H}:** {b[I]}W-{b[L]}L-{b[M]}D",inline=e)
	if R[F]+R[J]>0:S.add_field(name='🎯 Kill Comparison',value=f"**{D}:** {R[F]} kills\n**{H}:** {R[J]} kills",inline=C)
	S.add_field(name='📈 Overall Stats Comparison',value=f"**Wins:** {Y[O]} vs {a[O]}\n**Points:** {Y[K]:.1f} vs {a[K]:.1f}\n**K/D:** {Y[i]:.2f} vs {a[i]:.2f}",inline=C);T=[]
	for Q in A[B]:
		if Q[U]==D and Q[Z]==H or Q[U]==H and Q[Z]==D:T.append(Q)
	if T:
		T=T[-3:];f=N
		for Q in T:f+=f"**{Q[U]}** {Q[n]} on {Q[V]}\n"
		S.add_field(name='📅 Recent Matches',value=f,inline=e)
	await W.send(embed=S)
@D.command(name=Q)
async def AH(ctx):
	if not A[Q]:await ctx.send('❌ No tournament records available. Use `!refresh` to load data.');return
	C=E.Embed(title='🏆 Tournament Records',color=16766720);D=N
	for(F,B)in A[Q].items():
		if B[w]and B[x]:D+=f"**{F}:** {B[w]} ({B[x]})\n"
	C.description=D;C.set_footer(text='🔥 Hall of Fame - Elite Tournament Achievements');await ctx.send(embed=C)
@D.command(name=B,aliases=['recent','latest'])
async def AI(ctx,limit=10):
	D=limit
	if not A[B]:await ctx.send(q);return
	D=min(X(D,1),20);G=A[B][-D:];F=E.Embed(title=f"📅 Recent Matches (Last {D})",color=7506394)
	for(H,C)in t(s(G),1):I=f"**{C[U]}** {C[n]} **{C[Z]}**";J=f"📍 {C[V]} ({C[a]}) | 🎯 {C[R]}-{C[S]} | 📊 {C[v]:.1f} pts";F.add_field(name=f"#{H}",value=f"{I}\n{J}",inline=e)
	await ctx.send(embed=F)
@D.command(name='search')
async def AJ(ctx,*,query):
	G=ctx;D=query
	if not A[B]:await G.send(q);return
	F=[]
	for C in A[B]:
		if D.lower()in C[U].lower()or D.lower()in C[Z].lower():F.append(C)
	if not F:await G.send(f"❌ No matches found for '{D}'");return
	I=F[-10:];H=E.Embed(title=f"🔍 Match Search Results for '{D}'",description=f"Found {W(F)} matches (showing last 10)",color=10040012)
	for(J,C)in t(s(I),1):K=f"**{C[U]}** {C[n]} **{C[Z]}**";L=f"📍 {C[V]} ({C[a]}) | 🎯 {C[R]}-{C[S]}";H.add_field(name=f"#{J}",value=f"{K}\n{L}",inline=e)
	await G.send(embed=H)
@D.command(name=b)
async def AK(ctx):
	if not A[B]:await ctx.send(q);return
	F=f(lambda:{B:0,k:0})
	for G in A[B]:D=G[V];F[D][B]+=1;F[D][k]+=G[R]+G[S]
	J=Y(F.items(),key=lambda x:x[1][B],reverse=C);I=E.Embed(title='🗺️ Map Statistics',color=65407)
	for(D,H)in J:K=H[k]/X(H[B],1);I.add_field(name=D,value=f"**Matches:** {H[B]}\n**Avg Kills:** {K:.1f}",inline=C)
	await ctx.send(embed=I)
@D.command(name=c)
async def AL(ctx):
	if not A[B]:await ctx.send(q);return
	G=f(lambda:{B:0,k:0})
	for H in A[B]:D=H[a];G[D][B]+=1;G[D][k]+=H[R]+H[S]
	I=E.Embed(title='🌍 Regional Statistics',color=2003199)
	for(D,F)in G.items():
		if F[B]>0:J=F[k]/F[B];I.add_field(name=D,value=f"**Matches:** {F[B]}\n**Avg Kills:** {J:.1f}",inline=C)
	await ctx.send(embed=I)
@D.command(name='help')
async def AM(ctx):
	A=E.Embed(title='🤖 BTEL Tournament Bot Commands',description='Advanced Discord bot for tournament management',color=7506394);B=[('🔄 `!refresh`','Refresh tournament data from Google Sheets'),('🏆 `!leaderboard [sort]`','Display tournament leaderboard\nSort options: points, wins, kills, kd, matches'),('📊 `!player <name>`','Display detailed player statistics'),('⚔️ `!h2h <player1> <player2>`','Head-to-head comparison'),('🏅 `!records`','Display tournament records'),('📅 `!matches [limit]`','Show recent matches (default: 10)'),('🔍 `!search <player>`','Search matches for a player'),('🗺️ `!maps`','Display map statistics'),('🌍 `!regions`','Display regional statistics'),('❓ `!help`','Show this help message')]
	for(C,D)in B:A.add_field(name=C,value=D,inline=e)
	A.set_footer(text='🔥 Built for BTEL - Challenger Ascent Tournament');await ctx.send(embed=A)
@D.event
async def AN(ctx,error):
	B=error;A=ctx
	if A5(B,r.CommandNotFound):await A.send('❌ Command not found. Use `!help` to see available commands.')
	elif A5(B,r.MissingRequiredArgument):await A.send(f"❌ Missing required argument. Use `!help` for command usage.")
	else:H(f"Error: {B}");await A.send('❌ An error occurred while processing your command.')
@D.event
async def AO():
	if g.session:await g.session.close()
if __name__=='__main__':
	A4=os.getenv('DISCORD_TOKEN')
	if not A4:H('❌ Error: DISCORD_TOKEN environment variable not set!');H('Please set your Discord bot token as an environment variable:');H("export DISCORD_TOKEN='your_bot_token_here'");exit(1)
	try:D.run(A4)
	except KeyboardInterrupt:H('\n🛑 Bot shutdown requested by user')
	except l as AA:H(f"❌ Bot error: {AA}")
	finally:
		if g.session:AB=asyncio.get_event_loop();AB.run_until_complete(g.session.close())
		H('✅ aiohttp session closed.')
