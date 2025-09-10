import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import * as Constants from 'expo-constants';

const EXPO_PUBLIC_BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

export default function AdminLogin() {
  const [loading, setLoading] = useState(false);

  const handleGoogleLogin = async () => {
    setLoading(true);
    try {
      // Check authentication status
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/status`);
      const authData = await response.json();

      if (authData.authenticated) {
        router.replace('/admin/dashboard');
      } else {
        Alert.alert(
          'Authentication Required',
          'Emergent Google OAuth is being set up. For now, click "Continue as Admin" to proceed to the admin panel.',
          [
            { text: 'Cancel', style: 'cancel' },
            { 
              text: 'Continue as Admin', 
              onPress: () => router.replace('/admin/dashboard')
            },
          ]
        );
      }
    } catch (error) {
      console.error('Auth error:', error);
      Alert.alert(
        'Authentication Error',
        'For development purposes, you can continue as admin.',
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Continue as Admin', 
            onPress: () => router.replace('/admin/dashboard')
          },
        ]
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Text style={styles.backButtonText}>← Back to Home</Text>
          </TouchableOpacity>
        </View>

        {/* Login Form */}
        <View style={styles.loginContainer}>
          <View style={styles.logoContainer}>
            <Text style={styles.logoText}>🔐</Text>
            <Text style={styles.title}>Admin Portal</Text>
            <Text style={styles.subtitle}>PM Connect 3.0</Text>
          </View>

          <View style={styles.loginContent}>
            <Text style={styles.welcomeText}>
              Welcome to the admin portal. Please authenticate to access event management features.
            </Text>

            <TouchableOpacity
              style={[styles.loginButton, loading && styles.loginButtonDisabled]}
              onPress={handleGoogleLogin}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="white" size="small" />
              ) : (
                <>
                  <Text style={styles.googleIcon}>🔍</Text>
                  <Text style={styles.loginButtonText}>Sign in with Google</Text>
                </>
              )}
            </TouchableOpacity>

            <View style={styles.infoSection}>
              <Text style={styles.infoTitle}>Admin Features:</Text>
              <View style={styles.featureList}>
                <Text style={styles.featureItem}>• Dashboard with event statistics</Text>
                <Text style={styles.featureItem}>• Bulk upload invitee lists</Text>
                <Text style={styles.featureItem}>• View and export RSVP responses</Text>
                <Text style={styles.featureItem}>• Manage event agenda</Text>
                <Text style={styles.featureItem}>• Gallery management</Text>
                <Text style={styles.featureItem}>• Cab allocation system</Text>
              </View>
            </View>
          </View>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>© 2025 Jakson Limited. Powered by AI.</Text>
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
  },
  header: {
    backgroundColor: '#dc3545',
    padding: 24,
  },
  backButton: {
    alignSelf: 'flex-start',
  },
  backButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  loginContainer: {
    flex: 1,
    padding: 24,
    justifyContent: 'center',
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 48,
  },
  logoText: {
    fontSize: 48,
    marginBottom: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 18,
    color: '#6c757d',
  },
  loginContent: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 32,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  welcomeText: {
    fontSize: 16,
    color: '#6c757d',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  loginButton: {
    backgroundColor: '#4285f4',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    marginBottom: 32,
  },
  loginButtonDisabled: {
    opacity: 0.6,
  },
  googleIcon: {
    fontSize: 18,
    marginRight: 12,
  },
  loginButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  infoSection: {
    borderTopWidth: 1,
    borderTopColor: '#e9ecef',
    paddingTop: 24,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 16,
  },
  featureList: {
    gap: 8,
  },
  featureItem: {
    fontSize: 14,
    color: '#6c757d',
    lineHeight: 20,
  },
  footer: {
    padding: 24,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    color: '#adb5bd',
  },
});