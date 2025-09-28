import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  SafeAreaView,
  ScrollView,
  RefreshControl,
} from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Group {
  id: string;
  group_code: string;
  group_name: string;
  created_date: string;
}

export default function HomeScreen() {
  const [recentGroups, setRecentGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    loadRecentGroups();
  }, []);

  const loadRecentGroups = async () => {
    try {
      const groups = await AsyncStorage.getItem('recent_groups');
      if (groups) {
        setRecentGroups(JSON.parse(groups));
      }
    } catch (error) {
      console.error('Error loading recent groups:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGroupPress = (groupId: string) => {
    router.push(`/group/${groupId}`);
  };

  const handleCreateGroup = () => {
    router.push('/group/create');
  };

  const handleJoinGroup = () => {
    router.push('/group/join');
  };

  const clearRecentGroups = async () => {
    Alert.alert(
      'Clear Recent Groups',
      'Are you sure you want to clear all recent groups?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            await AsyncStorage.removeItem('recent_groups');
            setRecentGroups([]);
          },
        },
      ]
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Board Game Tracker</Text>
          <Text style={styles.subtitle}>Track scores with friends</Text>
        </View>

        {/* Action Buttons */}
        <View style={styles.actionsContainer}>
          <TouchableOpacity
            style={[styles.actionButton, styles.primaryButton]}
            onPress={handleCreateGroup}
            activeOpacity={0.8}
          >
            <Ionicons name="add-circle" size={24} color="white" />
            <Text style={styles.primaryButtonText}>Create New Group</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionButton, styles.secondaryButton]}
            onPress={handleJoinGroup}
            activeOpacity={0.8}
          >
            <Ionicons name="people" size={24} color="#007AFF" />
            <Text style={styles.secondaryButtonText}>Join Existing Group</Text>
          </TouchableOpacity>
        </View>

        {/* Recent Groups */}
        {recentGroups.length > 0 && (
          <View style={styles.recentContainer}>
            <View style={styles.recentHeader}>
              <Text style={styles.sectionTitle}>Recent Groups</Text>
              <TouchableOpacity onPress={clearRecentGroups}>
                <Text style={styles.clearText}>Clear</Text>
              </TouchableOpacity>
            </View>

            {recentGroups.map((group) => (
              <TouchableOpacity
                key={group.id}
                style={styles.groupCard}
                onPress={() => handleGroupPress(group.id)}
                activeOpacity={0.7}
              >
                <View style={styles.groupInfo}>
                  <Text style={styles.groupName}>{group.group_name}</Text>
                  <Text style={styles.groupCode}>Code: {group.group_code}</Text>
                </View>
                <Ionicons name="chevron-forward" size={20} color="#666" />
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Empty State */}
        {recentGroups.length === 0 && (
          <View style={styles.emptyContainer}>
            <Ionicons name="game-controller" size={80} color="#ccc" />
            <Text style={styles.emptyTitle}>No Groups Yet</Text>
            <Text style={styles.emptySubtitle}>
              Create a new group or join an existing one to start tracking board game scores!
            </Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
  },
  actionsContainer: {
    gap: 16,
    marginBottom: 40,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    minHeight: 56,
  },
  primaryButton: {
    backgroundColor: '#007AFF',
  },
  secondaryButton: {
    backgroundColor: 'white',
    borderWidth: 2,
    borderColor: '#007AFF',
  },
  primaryButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: 'white',
    marginLeft: 8,
  },
  secondaryButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#007AFF',
    marginLeft: 8,
  },
  recentContainer: {
    marginBottom: 32,
  },
  recentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  clearText: {
    fontSize: 16,
    color: '#007AFF',
  },
  groupCard: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  groupInfo: {
    flex: 1,
  },
  groupName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  groupCode: {
    fontSize: 14,
    color: '#666',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#666',
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 16,
    color: '#999',
    textAlign: 'center',
    lineHeight: 22,
    paddingHorizontal: 32,
  },
});