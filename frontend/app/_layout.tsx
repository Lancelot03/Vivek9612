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
        <Stack.Screen name="index" />
        <Stack.Screen name="auth/login" />
        <Stack.Screen name="auth/change-password" />
        <Stack.Screen name="auth/office-type" />
        <Stack.Screen name="rsvp" />
        <Stack.Screen name="event-info" />
        <Stack.Screen name="gallery" />
        <Stack.Screen name="admin/dashboard" />
        <Stack.Screen name="admin/login" />
        <Stack.Screen name="admin/invitees" />
        <Stack.Screen name="admin/responses" />
        <Stack.Screen name="admin/agenda" />
        <Stack.Screen name="admin/gallery-admin" />
        <Stack.Screen name="admin/cab-allocations" />
      </Stack>
    </AuthProvider>
  );
}