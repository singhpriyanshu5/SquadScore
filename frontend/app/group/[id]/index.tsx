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
  Share,
} from 'react-native';
import { useRouter, useLocalSearchParams, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Group {
  id: string;
  group_code: string;
  group_name: string;
  created_date: string;
}

interface GroupStats {
  total_players: number;
  total_teams: number;
  total_games: number;
  most_played_game: string | null;
  top_player: {
    id: string;
    name: string;
    total_score: number;
    games_played: number;
    average_score: number;
  } | null;
}

export default function GroupDashboardScreen() {
  const [group, setGroup] = useState<Group | null>(null);
  const [stats, setStats] = useState<GroupStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();

  useFocusEffect(
    useCallback(() => {
      if (id) {
        loadGroupData();
      }
    }, [id])
  );

  const loadGroupData = async () => {
    try {
      await Promise.all([loadGroup(), loadStats()]);
    } catch (error) {
      console.error('Error loading group data:', error);
      Alert.alert('Error', 'Failed to load group data. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const loadGroup = async () => {
    const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/groups/${id}`);
    if (!response.ok) {
      throw new Error('Failed to load group');
    }
    const groupData = await response.json();
    setGroup(groupData);
  };

  const loadStats = async () => {
    const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/groups/${id}/stats`);
    if (!response.ok) {
      throw new Error('Failed to load stats');
    }
    const statsData = await response.json();
    setStats(statsData);
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadGroupData();
  };

  const handleShareGroup = async () => {
    if (!group) return;

    const message = `Join my board game group "${group.group_name}"!\n\nGroup Code: ${group.group_code}\n\nUse this code in the Board Game Tracker app to join our group and start tracking scores together!`;

    try {
      await Share.share({
        message,
        title: `Join ${group.group_name}`,
      });
    } catch (error) {
      console.error('Error sharing:', error);
    }
  };

  const navigateToPlayers = () => {
    router.push(`/group/${id}/players`);
  };

  const navigateToTeams = () => {
    router.push(`/group/${id}/teams`);
  };

  const navigateToGame = () => {
    router.push(`/group/${id}/game`);
  };

  const navigateToLeaderboard = () => {
    router.push(`/group/${id}/leaderboard`);
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading group...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!group || !stats) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Ionicons name="alert-circle" size={64} color="#ff4444" />
          <Text style={styles.errorTitle}>Group not found</Text>
          <TouchableOpacity
            style={styles.retryButton}
            onPress={loadGroupData}
          >
            <Text style={styles.retryButtonText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
      >
        {/* Group Header */}
        <View style={styles.header}>
          <View style={styles.groupInfo}>
            <Text style={styles.groupName}>{group.group_name}</Text>
            <Text style={styles.groupCode}>Code: {group.group_code}</Text>
          </View>
          <TouchableOpacity
            style={styles.shareButton}
            onPress={handleShareGroup}
            activeOpacity={0.7}
          >
            <Ionicons name="share" size={24} color="#007AFF" />
          </TouchableOpacity>
        </View>

        {/* Quick Stats */}
        <View style={styles.statsContainer}>
          <TouchableOpacity 
            style={styles.statCard}
            onPress={navigateToPlayers}
            activeOpacity={0.7}
          >
            <Text style={styles.statNumber}>{stats.total_players}</Text>
            <Text style={styles.statLabel}>Players</Text>
            <Ionicons name="chevron-forward" size={16} color="#007AFF" style={styles.statChevron} />
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.statCard}
            onPress={navigateToTeams}
            activeOpacity={0.7}
          >
            <Text style={styles.statNumber}>{stats.total_teams}</Text>
            <Text style={styles.statLabel}>Teams</Text>
            <Ionicons name="chevron-forward" size={16} color="#007AFF" style={styles.statChevron} />
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.statCard}
            onPress={() => router.push(`/group/${id}/games`)}
            activeOpacity={0.7}
          >
            <Text style={styles.statNumber}>{stats.total_games}</Text>
            <Text style={styles.statLabel}>Games</Text>
            <Ionicons name="chevron-forward" size={16} color="#007AFF" style={styles.statChevron} />
          </TouchableOpacity>
        </View>

        {/* Top Player & Most Played Game */}
        {(stats.top_player || stats.most_played_game) && (
          <View style={styles.highlightsContainer}>
            {stats.top_player && (
              <View style={styles.highlightCard}>
                <Ionicons name="trophy" size={24} color="#ffd700" />
                <View style={styles.highlightInfo}>
                  <Text style={styles.highlightTitle}>Top Player</Text>
                  <Text style={styles.highlightValue}>{stats.top_player.name}</Text>
                  <Text style={styles.highlightSubtext}>{stats.top_player.total_score} points</Text>
                </View>
              </View>
            )}
            
            {stats.most_played_game && (
              <View style={styles.highlightCard}>
                <Ionicons name="game-controller" size={24} color="#007AFF" />
                <View style={styles.highlightInfo}>
                  <Text style={styles.highlightTitle}>Most Played</Text>
                  <Text style={styles.highlightValue}>{stats.most_played_game}</Text>
                </View>
              </View>
            )}
          </View>
        )}

        {/* Action Buttons */}
        <View style={styles.actionsContainer}>
          <TouchableOpacity
            style={[styles.actionButton, styles.primaryAction]}
            onPress={navigateToGame}
            activeOpacity={0.8}
          >
            <Ionicons name="add-circle" size={24} color="white" />
            <Text style={styles.primaryActionText}>Record New Game</Text>
          </TouchableOpacity>

          <View style={styles.secondaryActions}>
            <TouchableOpacity
              style={styles.secondaryActionButton}
              onPress={navigateToPlayers}
              activeOpacity={0.8}
            >
              <Ionicons name="person" size={24} color="#007AFF" />
              <Text style={styles.secondaryActionText}>Players</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.secondaryActionButton}
              onPress={navigateToTeams}
              activeOpacity={0.8}
            >
              <Ionicons name="people" size={24} color="#007AFF" />
              <Text style={styles.secondaryActionText}>Teams</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.secondaryActionButton}
              onPress={navigateToLeaderboard}
              activeOpacity={0.8}
            >
              <Ionicons name="podium" size={24} color="#007AFF" />
              <Text style={styles.secondaryActionText}>Leaderboard</Text>
            </TouchableOpacity>
          </View>
        </View>
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
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#666',
    marginTop: 16,
    marginBottom: 24,
  },
  retryButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
    marginBottom: 20,
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
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  groupCode: {
    fontSize: 16,
    color: '#666',
  },
  shareButton: {
    padding: 8,
  },
  statsContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 20,
  },
  statCard: {
    flex: 1,
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statNumber: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
  },
  highlightsContainer: {
    gap: 12,
    marginBottom: 32,
  },
  highlightCard: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  highlightInfo: {
    marginLeft: 16,
    flex: 1,
  },
  highlightTitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  highlightValue: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 2,
  },
  highlightSubtext: {
    fontSize: 14,
    color: '#666',
  },
  actionsContainer: {
    gap: 16,
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
  primaryAction: {
    backgroundColor: '#007AFF',
  },
  primaryActionText: {
    fontSize: 18,
    fontWeight: '600',
    color: 'white',
    marginLeft: 8,
  },
  secondaryActions: {
    flexDirection: 'row',
    gap: 12,
  },
  secondaryActionButton: {
    flex: 1,
    backgroundColor: 'white',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 12,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#e1e5e9',
    minHeight: 56,
  },
  secondaryActionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
    marginTop: 4,
  },
});