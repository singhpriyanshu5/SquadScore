import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  Alert,
  SafeAreaView,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useLocalSearchParams, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface PlayerScore {
  player_id: string;
  player_name: string;
  score: number;
}

interface TeamScore {
  team_id: string;
  team_name: string;
  score: number;
  player_ids: string[];
}

interface GameSession {
  id: string;
  group_id: string;
  game_name: string;
  game_date: string;
  player_scores?: PlayerScore[];
  team_scores?: TeamScore[];
  created_date: string;
}

export default function GamesHistoryScreen() {
  const [gameSessions, setGameSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [deletingSessionId, setDeletingSessionId] = useState(null);
  const { id } = useLocalSearchParams();

  useFocusEffect(
    useCallback(() => {
      if (id) {
        loadGameSessions();
      }
    }, [id])
  );

  const loadGameSessions = async () => {
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/groups/${id}/game-sessions-with-normalized`);
      if (!response.ok) {
        throw new Error('Failed to load game sessions');
      }
      const sessions = await response.json();
      setGameSessions(sessions);
    } catch (error) {
      console.error('Error loading game sessions:', error);
      Alert.alert('Error', 'Failed to load game sessions. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadGameSessions();
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM d, yyyy');
    } catch {
      return 'Unknown date';
    }
  };

  const formatTime = (dateString: string) => {
    try {
      return format(new Date(dateString), 'h:mm a');
    } catch {
      return '';
    }
  };

  const handleDeleteGame = (session: GameSession) => {
    Alert.alert(
      'Delete Game',
      `Are you sure you want to delete this "${session.game_name}" game? This will remove all scores and update player statistics.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => confirmDeleteGame(session.id),
        },
      ]
    );
  };

  const confirmDeleteGame = async (sessionId: string) => {
    setDeletingSessionId(sessionId);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/game-sessions/${sessionId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete game session');
      }

      loadGameSessions();
    } catch (error) {
      console.error('Error deleting game session:', error);
      Alert.alert('Error', 'Failed to delete game session. Please try again.');
    } finally {
      setDeletingSessionId(null);
    }
  };

  const getTotalPlayers = (session: GameSession) => {
    const individualPlayers = session.player_scores?.length || 0;
    const teamPlayers = session.team_scores?.reduce((sum, team) => sum + team.player_ids.length, 0) || 0;
    return individualPlayers + teamPlayers;
  };

  const getHighestScore = (session: GameSession) => {
    const playerScores = session.player_scores?.map(p => p.score) || [];
    const teamScores = session.team_scores?.map(t => t.score) || [];
    const allScores = [...playerScores, ...teamScores];
    return allScores.length > 0 ? Math.max(...allScores) : 0;
  };

  const getWinner = (session: GameSession) => {
    let winner = '';
    let highestScore = -Infinity;

    // Check individual players
    session.player_scores?.forEach(player => {
      if (player.score > highestScore) {
        highestScore = player.score;
        winner = player.player_name;
      }
    });

    // Check teams
    session.team_scores?.forEach(team => {
      if (team.score > highestScore) {
        highestScore = team.score;
        winner = team.team_name;
      }
    });

    return winner || 'No scores recorded';
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading game history...</Text>
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
        {gameSessions.length > 0 ? (
          <View style={styles.gamesContainer}>
            <Text style={styles.sectionTitle}>Game History ({gameSessions.length} games)</Text>
            
            {gameSessions.map((session) => (
              <View key={session.id} style={styles.gameCard}>
                <View style={styles.gameHeader}>
                  <View style={styles.gameInfo}>
                    <Text style={styles.gameName}>{session.game_name}</Text>
                    <Text style={styles.gameDate}>
                      {formatDate(session.game_date)} • {formatTime(session.created_date)}
                    </Text>
                  </View>
                  <View style={styles.gameActions}>
                    <View style={styles.gameIcon}>
                      <Ionicons name="grid-outline" size={24} color="#007AFF" />
                    </View>
                    <TouchableOpacity
                      style={styles.deleteGameButton}
                      onPress={() => handleDeleteGame(session)}
                      disabled={deletingSessionId === session.id}
                      activeOpacity={0.7}
                    >
                      {deletingSessionId === session.id ? (
                        <ActivityIndicator size="small" color="#ff4444" />
                      ) : (
                        <Ionicons name="trash" size={20} color="#ff4444" />
                      )}
                    </TouchableOpacity>
                  </View>
                </View>

                <View style={styles.gameStats}>
                  <View style={styles.statItem}>
                    <Text style={styles.statValue}>{getTotalPlayers(session)}</Text>
                    <Text style={styles.statLabel}>Players</Text>
                  </View>
                  <View style={styles.statItem}>
                    <Text style={styles.statValue}>{getHighestScore(session)}</Text>
                    <Text style={styles.statLabel}>High Score</Text>
                  </View>
                  <View style={styles.statItem}>
                    <Text style={styles.statValue}>👑</Text>
                    <Text style={styles.statLabel}>{getWinner(session)}</Text>
                  </View>
                </View>

                {/* Individual Player Scores */}
                {session.player_scores && session.player_scores.length > 0 && (
                  <View style={styles.scoresSection}>
                    <Text style={styles.scoresSectionTitle}>Individual Players</Text>
                    <View style={styles.scoresList}>
                      {session.player_scores.map((player, index) => (
                        <View key={index} style={styles.scoreItem}>
                          <Text style={styles.scoreName}>{player.player_name}</Text>
                          <View style={styles.scoreValues}>
                            <Text style={styles.scoreValue}>{player.normalized_score || 'N/A'}</Text>
                            <Text style={styles.scoreSubValue}>({player.score})</Text>
                          </View>
                        </View>
                      ))}
                    </View>
                  </View>
                )}

                {/* Team Scores */}
                {session.team_scores && session.team_scores.length > 0 && (
                  <View style={styles.scoresSection}>
                    <Text style={styles.scoresSectionTitle}>Teams</Text>
                    <View style={styles.scoresList}>
                      {session.team_scores.map((team, index) => (
                        <View key={index} style={styles.scoreItem}>
                          <Text style={styles.scoreName}>{team.team_name}</Text>
                          <View style={styles.scoreValues}>
                            <Text style={styles.scoreValue}>{team.normalized_score || 'N/A'}</Text>
                            <Text style={styles.scoreSubValue}>({team.score})</Text>
                          </View>
                        </View>
                      ))}
                    </View>
                  </View>
                )}
              </View>
            ))}
          </View>
        ) : (
          <View style={styles.emptyContainer}>
            <Ionicons name="grid-outline" size={80} color="#ccc" />
            <Text style={styles.emptyTitle}>No Games Recorded</Text>
            <Text style={styles.emptySubtitle}>
              Start recording games to see your group's game history here!
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
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
  },
  gamesContainer: {
    gap: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  gameCard: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  gameHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  gameInfo: {
    flex: 1,
  },
  gameName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  gameDate: {
    fontSize: 14,
    color: '#666',
  },
  gameActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  gameIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#e3f2fd',
    alignItems: 'center',
    justifyContent: 'center',
  },
  deleteGameButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#ffe6e6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  gameStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    marginBottom: 16,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  scoresSection: {
    marginBottom: 12,
  },
  scoresSectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  scoresList: {
    gap: 6,
  },
  scoreItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
    paddingHorizontal: 8,
    backgroundColor: '#f8f9fa',
    borderRadius: 6,
  },
  scoreName: {
    fontSize: 14,
    color: '#1a1a1a',
    flex: 1,
  },
  scoreValues: {
    alignItems: 'flex-end',
  },
  scoreValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },
  scoreSubValue: {
    fontSize: 11,
    color: '#666',
    marginTop: 2,
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