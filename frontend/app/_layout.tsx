import React from 'react';
import { Stack } from 'expo-router';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <Stack
        screenOptions={{
          headerShown: false,
        }}
      >
        <Stack.Screen name="index" options={{ title: 'Home' }} />
        <Stack.Screen name="test" options={{ title: 'Test Page' }} />
        <Stack.Screen name="auth/login" options={{ title: 'Login' }} />
        <Stack.Screen name="auth/change-password" options={{ title: 'Change Password' }} />
        <Stack.Screen name="auth/set-office-type" options={{ title: 'Office Type' }} />
        <Stack.Screen name="rsvp" options={{ title: 'RSVP' }} />
        <Stack.Screen name="event-info" options={{ title: 'Event Info' }} />
        <Stack.Screen name="gallery" options={{ title: 'Gallery' }} />
        <Stack.Screen name="admin/dashboard" options={{ title: 'Admin Dashboard' }} />
        <Stack.Screen name="admin/invitees" options={{ title: 'Manage Invitees' }} />
        <Stack.Screen name="admin/responses" options={{ title: 'Manage Responses' }} />
        <Stack.Screen name="admin/agenda" options={{ title: 'Manage Agenda' }} />
        <Stack.Screen name="admin/gallery-admin" options={{ title: 'Manage Gallery' }} />
        <Stack.Screen name="admin/cab-allocations" options={{ title: 'Manage Cab Allocations' }} />
      </Stack>
    </GestureHandlerRootView>
  );
}