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
import { useLocalSearchParams, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface LeaderboardEntry {
  id: string;
  name: string;
  total_score: number;
  games_played: number;
  average_score: number;
}

type LeaderboardType = 'players' | 'teams';

export default function LeaderboardScreen() {
  const [playerLeaderboard, setPlayerLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [teamLeaderboard, setTeamLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<LeaderboardType>('players');
  const { id } = useLocalSearchParams<{ id: string }>();

  useFocusEffect(
    useCallback(() => {
      if (id) {
        loadLeaderboards();
      }
    }, [id])
  );

  const loadLeaderboards = async () => {
    try {
      await Promise.all([loadPlayerLeaderboard(), loadTeamLeaderboard()]);
    } catch (error) {
      console.error('Error loading leaderboards:', error);
      Alert.alert('Error', 'Failed to load leaderboards. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const loadPlayerLeaderboard = async () => {
    const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/groups/${id}/leaderboard/players`);
    if (!response.ok) {
      throw new Error('Failed to load player leaderboard');
    }
    const data = await response.json();
    setPlayerLeaderboard(data);
  };

  const loadTeamLeaderboard = async () => {
    const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/groups/${id}/leaderboard/teams`);
    if (!response.ok) {
      throw new Error('Failed to load team leaderboard');
    }
    const data = await response.json();
    setTeamLeaderboard(data);
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadLeaderboards();
  };

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return { name: 'trophy' as const, color: '#ffd700' };
      case 2:
        return { name: 'medal' as const, color: '#c0c0c0' };
      case 3:
        return { name: 'medal' as const, color: '#cd7f32' };
      default:
        return { name: 'ellipse' as const, color: '#666' };
    }
  };

  const renderLeaderboardEntry = (entry: LeaderboardEntry, index: number) => {
    const rank = index + 1;
    const icon = getRankIcon(rank);
    
    return (
      <View key={entry.id} style={[
        styles.entryCard,
        rank <= 3 && styles.topEntryCard
      ]}>
        <View style={styles.rankContainer}>
          <Ionicons name={icon.name} size={24} color={icon.color} />
          <Text style={[
            styles.rankText,
            rank <= 3 && styles.topRankText
          ]}>
            #{rank}
          </Text>
        </View>
        
        <View style={styles.entryInfo}>
          <Text style={[
            styles.entryName,
            rank <= 3 && styles.topEntryName
          ]}>
            {entry.name}
          </Text>
          
          <View style={styles.entryStats}>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{entry.total_score}</Text>
              <Text style={styles.statLabel}>Total</Text>
            </View>
            
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{entry.games_played}</Text>
              <Text style={styles.statLabel}>Games</Text>
            </View>
            
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{entry.average_score}</Text>
              <Text style={styles.statLabel}>Avg</Text>
            </View>
          </View>
        </View>
        
        {rank <= 3 && (
          <View style={[styles.crownContainer, { opacity: 4 - rank }]}>
            <Ionicons name="ribbon" size={20} color={icon.color} />
          </View>
        )}
      </View>
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading leaderboards...</Text>
        </View>
      </SafeAreaView>
    );
  }

  const currentLeaderboard = activeTab === 'players' ? playerLeaderboard : teamLeaderboard;
  const hasData = currentLeaderboard.length > 0;

  return (
    <SafeAreaView style={styles.container}>
      {/* Tab Selector */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[
            styles.tab,
            activeTab === 'players' && styles.activeTab
          ]}
          onPress={() => setActiveTab('players')}
          activeOpacity={0.7}
        >
          <Ionicons 
            name="person" 
            size={20} 
            color={activeTab === 'players' ? 'white' : '#007AFF'} 
          />
          <Text style={[
            styles.tabText,
            activeTab === 'players' && styles.activeTabText
          ]}>
            Players
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[
            styles.tab,
            activeTab === 'teams' && styles.activeTab
          ]}
          onPress={() => setActiveTab('teams')}
          activeOpacity={0.7}
        >
          <Ionicons 
            name="people" 
            size={20} 
            color={activeTab === 'teams' ? 'white' : '#007AFF'} 
          />
          <Text style={[
            styles.tabText,
            activeTab === 'teams' && styles.activeTabText
          ]}>
            Teams
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
      >
        {hasData ? (
          <View style={styles.leaderboardContainer}>
            <Text style={styles.sectionTitle}>
              {activeTab === 'players' ? 'Player Rankings' : 'Team Rankings'}
            </Text>
            
            {currentLeaderboard.map((entry, index) => 
              renderLeaderboardEntry(entry, index)
            )}
            
            {currentLeaderboard.length > 0 && (
              <View style={styles.statsFooter}>
                <Text style={styles.footerText}>
                  Total {activeTab}: {currentLeaderboard.length}
                </Text>
                <Text style={styles.footerText}>
                  Highest Score: {Math.max(...currentLeaderboard.map(e => e.total_score))}
                </Text>
              </View>
            )}
          </View>
        ) : (
          <View style={styles.emptyContainer}>
            <Ionicons 
              name={activeTab === 'players' ? 'person' : 'people'} 
              size={80} 
              color="#ccc" 
            />
            <Text style={styles.emptyTitle}>
              No {activeTab === 'players' ? 'Player' : 'Team'} Data
            </Text>
            <Text style={styles.emptySubtitle}>
              {activeTab === 'players' 
                ? 'Add players and record games to see player rankings!' 
                : 'Create teams and record team games to see team rankings!'
              }
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
  tabContainer: {
    flexDirection: 'row',
    margin: 20,
    marginBottom: 0,
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    gap: 8,
  },
  activeTab: {
    backgroundColor: '#007AFF',
  },
  tabText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  activeTabText: {
    color: 'white',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
  },
  leaderboardContainer: {
    gap: 12,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
    textAlign: 'center',
  },
  entryCard: {
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
    position: 'relative',
  },
  topEntryCard: {
    borderWidth: 2,
    borderColor: '#ffd700',
    backgroundColor: '#fffef7',
  },
  rankContainer: {
    alignItems: 'center',
    marginRight: 16,
    width: 40,
  },
  rankText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#666',
    marginTop: 4,
  },
  topRankText: {
    color: '#ffd700',
  },
  entryInfo: {
    flex: 1,
  },
  entryName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  topEntryName: {
    color: '#b8860b',
  },
  entryStats: {
    flexDirection: 'row',
    gap: 24,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 2,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
  },
  crownContainer: {
    position: 'absolute',
    top: -8,
    right: 16,
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 4,
  },
  statsFooter: {
    backgroundColor: '#e3f2fd',
    padding: 16,
    borderRadius: 12,
    marginTop: 16,
    alignItems: 'center',
    gap: 4,
  },
  footerText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
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