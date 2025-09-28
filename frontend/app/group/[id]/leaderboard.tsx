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
  Modal,
} from 'react-native';
import { useLocalSearchParams, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface LeaderboardEntry {
  id: string;
  name: string;
  total_score: number; // Normalized score
  games_played: number;
  average_score: number; // Normalized average
  raw_total_score?: number; // Actual scores entered
  raw_average_score?: number; // Actual average scores
}

type LeaderboardType = 'players' | 'teams';

export default function LeaderboardScreen() {
  const [playerLeaderboard, setPlayerLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [teamLeaderboard, setTeamLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<LeaderboardType>('players');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedGame, setSelectedGame] = useState<string>('');
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [selectedMonth, setSelectedMonth] = useState<number | null>(null);
  const [availableGames, setAvailableGames] = useState<string[]>([]);
  const { id } = useLocalSearchParams<{ id: string }>();

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);
  const months = [
    { value: 1, label: 'January' },
    { value: 2, label: 'February' },
    { value: 3, label: 'March' },
    { value: 4, label: 'April' },
    { value: 5, label: 'May' },
    { value: 6, label: 'June' },
    { value: 7, label: 'July' },
    { value: 8, label: 'August' },
    { value: 9, label: 'September' },
    { value: 10, label: 'October' },
    { value: 11, label: 'November' },
    { value: 12, label: 'December' },
  ];

  useFocusEffect(
    useCallback(() => {
      if (id) {
        loadLeaderboards();
      }
    }, [id])
  );

  const loadLeaderboards = async () => {
    try {
      await Promise.all([loadPlayerLeaderboard(), loadTeamLeaderboard(), loadAvailableGames()]);
    } catch (error) {
      console.error('Error loading leaderboards:', error);
      Alert.alert('Error', 'Failed to load leaderboards. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const buildFilterParams = () => {
    const params = new URLSearchParams();
    if (selectedGame) {
      params.append('game_name', selectedGame);
    }
    if (selectedYear) {
      params.append('year', selectedYear.toString());
    }
    if (selectedMonth) {
      params.append('month', selectedMonth.toString());
    }
    return params.toString();
  };

  const loadPlayerLeaderboard = async () => {
    const filterParams = buildFilterParams();
    const url = `${EXPO_PUBLIC_BACKEND_URL}/api/groups/${id}/leaderboard/players${filterParams ? '?' + filterParams : ''}`;
    const response = await fetch(url);
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

  const loadAvailableGames = async () => {
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/groups/${id}/games`);
      if (response.ok) {
        const games = await response.json();
        setAvailableGames(games);
      }
    } catch (error) {
      console.error('Error loading available games:', error);
    }
  };

  const applyFilters = async () => {
    setLoading(true);
    try {
      await loadPlayerLeaderboard();
    } catch (error) {
      console.error('Error applying filters:', error);
      Alert.alert('Error', 'Failed to apply filters. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = async () => {
    setSelectedGame('');
    setSelectedYear(null);
    setSelectedMonth(null);
    setLoading(true);
    try {
      await loadPlayerLeaderboard();
    } catch (error) {
      console.error('Error clearing filters:', error);
      Alert.alert('Error', 'Failed to clear filters. Please try again.');
    } finally {
      setLoading(false);
    }
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
              <Text style={styles.statSubValue}>({entry.raw_total_score || 0})</Text>
              <Text style={styles.statLabel}>Total</Text>
            </View>
            
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{entry.games_played}</Text>
              <Text style={styles.statLabel}>Games</Text>
            </View>
            
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{entry.average_score}</Text>
              <Text style={styles.statSubValue}>({entry.raw_average_score || 0})</Text>
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
      {/* Tab Selector with Filter Button */}
      <View style={styles.headerContainer}>
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

        {/* Filter Button */}
        <TouchableOpacity
          style={styles.filterButton}
          onPress={() => setShowFilters(true)}
          activeOpacity={0.7}
        >
          <Ionicons 
            name="funnel" 
            size={20} 
            color={(selectedGame || selectedYear || selectedMonth) ? '#007AFF' : '#666'} 
          />
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
            
            <View style={styles.infoContainer}>
              <Ionicons name="information-circle-outline" size={16} color="#666" />
              <Text style={styles.infoText}>
                Scores are normalized (0-1) per game to ensure fair rankings across different game types
              </Text>
            </View>
            
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

      {/* Filter Modal */}
      <Modal
        visible={showFilters}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowFilters(false)}
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setShowFilters(false)}>
              <Text style={styles.modalCancel}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Filter Leaderboard</Text>
            <TouchableOpacity onPress={clearFilters}>
              <Text style={styles.modalClear}>Clear</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalBody}>
            {/* Game Filter */}
            <View style={styles.filterSection}>
              <Text style={styles.filterLabel}>Game</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.gameOptions}>
                <TouchableOpacity
                  style={[styles.gameOption, !selectedGame && styles.gameOptionSelected]}
                  onPress={() => setSelectedGame('')}
                >
                  <Text style={[styles.gameOptionText, !selectedGame && styles.gameOptionTextSelected]}>
                    All Games
                  </Text>
                </TouchableOpacity>
                {availableGames.map((game) => (
                  <TouchableOpacity
                    key={game}
                    style={[styles.gameOption, selectedGame === game && styles.gameOptionSelected]}
                    onPress={() => setSelectedGame(game)}
                  >
                    <Text style={[styles.gameOptionText, selectedGame === game && styles.gameOptionTextSelected]}>
                      {game}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>

            {/* Year Filter */}
            <View style={styles.filterSection}>
              <Text style={styles.filterLabel}>Year</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.yearOptions}>
                <TouchableOpacity
                  style={[styles.yearOption, !selectedYear && styles.yearOptionSelected]}
                  onPress={() => setSelectedYear(null)}
                >
                  <Text style={[styles.yearOptionText, !selectedYear && styles.yearOptionTextSelected]}>
                    All Years
                  </Text>
                </TouchableOpacity>
                {years.map((year) => (
                  <TouchableOpacity
                    key={year}
                    style={[styles.yearOption, selectedYear === year && styles.yearOptionSelected]}
                    onPress={() => setSelectedYear(year)}
                  >
                    <Text style={[styles.yearOptionText, selectedYear === year && styles.yearOptionTextSelected]}>
                      {year}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>

            {/* Month Filter */}
            {selectedYear && (
              <View style={styles.filterSection}>
                <Text style={styles.filterLabel}>Month</Text>
                <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.monthOptions}>
                  <TouchableOpacity
                    style={[styles.monthOption, !selectedMonth && styles.monthOptionSelected]}
                    onPress={() => setSelectedMonth(null)}
                  >
                    <Text style={[styles.monthOptionText, !selectedMonth && styles.monthOptionTextSelected]}>
                      All Months
                    </Text>
                  </TouchableOpacity>
                  {months.map((month) => (
                    <TouchableOpacity
                      key={month.value}
                      style={[styles.monthOption, selectedMonth === month.value && styles.monthOptionSelected]}
                      onPress={() => setSelectedMonth(month.value)}
                    >
                      <Text style={[styles.monthOptionText, selectedMonth === month.value && styles.monthOptionTextSelected]}>
                        {month.label}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>
            )}

            <TouchableOpacity
              style={styles.applyButton}
              onPress={() => {
                setShowFilters(false);
                applyFilters();
              }}
            >
              <Text style={styles.applyButtonText}>Apply Filters</Text>
            </TouchableOpacity>
          </ScrollView>
        </SafeAreaView>
      </Modal>
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
  headerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    margin: 20,
    marginBottom: 0,
    gap: 12,
  },
  tabContainer: {
    flex: 1,
    flexDirection: 'row',
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  filterButton: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: 'white',
    alignItems: 'center',
    justifyContent: 'center',
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
  modalContainer: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e5e9',
  },
  modalCancel: {
    fontSize: 16,
    color: '#666',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  modalClear: {
    fontSize: 16,
    color: '#007AFF',
  },
  modalBody: {
    flex: 1,
    padding: 20,
  },
  filterSection: {
    marginBottom: 32,
  },
  filterLabel: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 12,
  },
  gameOptions: {
    flexDirection: 'row',
  },
  gameOption: {
    backgroundColor: 'white',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    marginRight: 12,
    borderWidth: 2,
    borderColor: '#e1e5e9',
  },
  gameOptionSelected: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  gameOptionText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  gameOptionTextSelected: {
    color: 'white',
  },
  yearOptions: {
    flexDirection: 'row',
  },
  yearOption: {
    backgroundColor: 'white',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    marginRight: 12,
    borderWidth: 2,
    borderColor: '#e1e5e9',
  },
  yearOptionSelected: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  yearOptionText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  yearOptionTextSelected: {
    color: 'white',
  },
  monthOptions: {
    flexDirection: 'row',
  },
  monthOption: {
    backgroundColor: 'white',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    marginRight: 12,
    borderWidth: 2,
    borderColor: '#e1e5e9',
  },
  monthOptionSelected: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  monthOptionText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  monthOptionTextSelected: {
    color: 'white',
  },
  applyButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 24,
  },
  applyButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: 'white',
  },
  infoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
    gap: 8,
  },
  infoText: {
    flex: 1,
    fontSize: 12,
    color: '#666',
    lineHeight: 16,
  },
});