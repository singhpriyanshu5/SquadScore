import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import React from 'react';

export default function RootLayout() {
  return (
    <>
      <StatusBar style="dark" backgroundColor="#fff" />
      <Stack
        screenOptions={{
          headerStyle: {
            backgroundColor: '#fff',
          },
          headerTintColor: '#000',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
          headerShadowVisible: false,
        }}
      >
        <Stack.Screen 
          name="index" 
          options={{ 
            title: 'Board Game Tracker',
            headerShown: true 
          }} 
        />
        <Stack.Screen 
          name="group/create" 
          options={{ 
            title: 'Create Group',
            presentation: 'modal' 
          }} 
        />
        <Stack.Screen 
          name="group/join" 
          options={{ 
            title: 'Join Group',
            presentation: 'modal' 
          }} 
        />
        <Stack.Screen 
          name="group/[id]/index" 
          options={{ 
            title: 'Group Dashboard'
          }} 
        />
        <Stack.Screen 
          name="group/[id]/players" 
          options={{ 
            title: 'Manage Players'
          }} 
        />
        <Stack.Screen 
          name="group/[id]/teams" 
          options={{ 
            title: 'Manage Teams'
          }} 
        />
        <Stack.Screen 
          name="group/[id]/game" 
          options={{ 
            title: 'Record Game'
          }} 
        />
        <Stack.Screen 
          name="group/[id]/leaderboard" 
          options={{ 
            title: 'Leaderboards'
          }} 
        />
      </Stack>
    </>
  );
}