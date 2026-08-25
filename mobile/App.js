import React, {useEffect, useState} from 'react';
import {SafeAreaView, ScrollView, Text, View, Pressable, StyleSheet} from 'react-native';
import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';

const API = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

async function registerPush() {
  const permissions = await Notifications.getPermissionsAsync();
  if (!permissions.granted) await Notifications.requestPermissionsAsync();
  if (Constants.isDevice) {
    const token = (await Notifications.getExpoPushTokenAsync()).data;
    await fetch(`${API}/api/notifications/register`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({token})});
  }
}

export default function App() {
  const [data, setData] = useState({updates:[], prices:[], wishlist:[], steam:{}, gamescom:{}});
  const load = async () => {
    const [updates, prices, wishlist, steam, gamescom] = await Promise.all(['updates','prices','wishlist'].map(x=>fetch(`${API}/api/${x}`).then(r=>r.json())).concat([fetch(`${API}/api/steam/profile`).then(r=>r.json()), fetch(`${API}/api/gamescom`).then(r=>r.json())]));
    setData({updates, prices, wishlist, steam, gamescom});
  };
  useEffect(()=>{registerPush().catch(()=>{}); load().catch(()=>{});},[]);
  return <SafeAreaView style={styles.root}><ScrollView contentContainerStyle={styles.content}>
    <Text style={styles.title}>🎮 Personal Gaming Assistant</Text>
    <Pressable style={styles.button} onPress={()=>fetch(`${API}/api/update`,{method:'POST'}).then(load)}><Text style={styles.buttonText}>🔄 Manual update</Text></Pressable>
    <Card title="📰 Laatste 6 updates">{data.updates.slice(0,6).map((x,i)=><Text style={styles.text} key={i}>{x.timestamp} · {x.type} · {x.status}</Text>)}</Card>
    <Card title="💰 Live prijzen">{data.prices.slice(0,20).map((x,i)=><Text style={styles.text} key={i}>{x.product} — {x.price||'—'} {x.currency||''} · {x.stock||'—'}</Text>)}</Card>
    <Card title="❤️ Wishlist">{data.wishlist.map((x,i)=><Text style={styles.text} key={i}>{x.category||'Game'} · {x.title}</Text>)}</Card>
    <Card title="🎮 Steam profiel"><Text style={styles.text}>{data.steam.display_name||'Niet gekoppeld'} · Level {data.steam.level||'—'} · {data.steam.games?.length||0} games</Text></Card>
    <Card title="🎟️ GamesCom"><Text style={styles.text}>{data.gamescom.status||'—'} · volgende: {data.gamescom.countdown_target||'—'}</Text></Card>
  </ScrollView></SafeAreaView>
}
function Card({title,children}) { return <View style={styles.card}><Text style={styles.heading}>{title}</Text>{children}</View> }
const styles=StyleSheet.create({root:{flex:1,backgroundColor:'#050807'},content:{padding:18,gap:14},title:{fontSize:25,fontWeight:'800',color:'#7cff9b'},card:{backgroundColor:'#0b1510',borderColor:'#1e6335',borderWidth:1,borderRadius:14,padding:16},heading:{color:'#57ff85',fontSize:18,fontWeight:'700',marginBottom:8},text:{color:'#d8ffe2',marginVertical:3},button:{backgroundColor:'#1ed760',padding:13,borderRadius:10,alignItems:'center'},buttonText:{color:'#001b09',fontWeight:'800'}});
