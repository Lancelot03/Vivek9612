import React from 'react';
import { Stack } from 'expo-router';
import { AuthProvider } from '../contexts/AuthContext';

export default function RootLayout() {
  return (
    <AuthProvider>
      <Stack
        screenOptions={{
          headerShown: false,
        }}
      >
        <Stack.Screen name="index" options={{ title: 'Home' }} />
        <Stack.Screen name="auth/login" options={{ title: 'Login' }} />
        <Stack.Screen name="auth/change-password" options={{ title: 'Change Password' }} />
        <Stack.Screen name="auth/office-type" options={{ title: 'Office Type' }} />
        <Stack.Screen name="rsvp" options={{ title: 'RSVP' }} />
        <Stack.Screen name="event-info" options={{ title: 'Event Info' }} />
        <Stack.Screen name="gallery" options={{ title: 'Gallery' }} />
        <Stack.Screen name="admin/dashboard" options={{ title: 'Admin Dashboard' }} />
        <Stack.Screen name="admin/login" options={{ title: 'Admin Login' }} />
        <Stack.Screen name="admin/invitees" options={{ title: 'Manage Invitees' }} />
        <Stack.Screen name="admin/responses" options={{ title: 'Manage Responses' }} />
        <Stack.Screen name="admin/agenda" options={{ title: 'Manage Agenda' }} />
        <Stack.Screen name="admin/gallery-admin" options={{ title: 'Manage Gallery' }} />
        <Stack.Screen name="admin/cab-allocations" options={{ title: 'Manage Cab Allocations' }} />
      </Stack>
    </AuthProvider>
  );
}