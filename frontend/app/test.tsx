import React from 'react';
import { View, Text, StyleSheet, SafeAreaView, TouchableOpacity } from 'react-native';
import { router } from 'expo-router';

export default function TestPage() {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>🎉 PM Connect 3.0 Test Page</Text>
        <Text style={styles.subtitle}>App is working correctly!</Text>
        
        <TouchableOpacity 
          style={styles.button}
          onPress={() => router.push('/')}
        >
          <Text style={styles.buttonText}>Go to Home</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={styles.button}
          onPress={() => router.push('/auth/login')}
        >
          <Text style={styles.buttonText}>Go to Login</Text>
        </TouchableOpacity>
        
        <View style={styles.infoSection}>
          <Text style={styles.infoTitle}>Available Routes:</Text>
          <Text style={styles.infoText}>• / (Home)</Text>
          <Text style={styles.infoText}>• /auth/login (Employee Login)</Text>
          <Text style={styles.infoText}>• /admin/dashboard (Admin Dashboard)</Text>
          <Text style={styles.infoText}>• /rsvp (RSVP Form)</Text>
          <Text style={styles.infoText}>• /gallery (Gallery)</Text>
          <Text style={styles.infoText}>• /event-info (Event Info)</Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  content: {
    flex: 1,
    padding: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#007bff',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 18,
    color: '#6c757d',
    marginBottom: 32,
    textAlign: 'center',
  },
  button: {
    backgroundColor: '#007bff',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    marginBottom: 16,
    minWidth: 200,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  infoSection: {
    marginTop: 32,
    padding: 20,
    backgroundColor: 'white',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e9ecef',
    alignSelf: 'stretch',
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 12,
  },
  infoText: {
    fontSize: 14,
    color: '#6c757d',
    marginBottom: 4,
  },
});