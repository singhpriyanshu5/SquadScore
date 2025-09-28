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
  Platform,
} from 'react-native';
import { useRouter, useLocalSearchParams, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as DocumentPicker from 'expo-document-picker';
import * as Sharing from 'expo-sharing';
import * as WebBrowser from 'expo-web-browser';

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
  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);
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

  const convertToCSV = (data: any) => {
    const lines = [];
    
    // Add group info header
    lines.push('GROUP INFORMATION');
    lines.push(`Group Name,${data.group.group_name}`);
    lines.push(`Group Code,${data.group.group_code}`);
    lines.push(`Export Date,${new Date().toISOString().split('T')[0]}`);
    lines.push('');
    
    // Add players section
    lines.push('PLAYERS');
    lines.push('Player Name,Emoji,Total Score,Games Played,Average Score,Joined Date');
    data.players.forEach((player: any) => {
      const avgScore = player.games_played > 0 ? (player.total_score / player.games_played).toFixed(2) : '0.00';
      const joinedDate = new Date(player.created_date).toISOString().split('T')[0];
      lines.push(`"${player.player_name}",${player.emoji},${player.total_score},${player.games_played},${avgScore},${joinedDate}`);
    });
    lines.push('');
    
    // Add teams section
    if (data.teams && data.teams.length > 0) {
      lines.push('TEAMS');
      lines.push('Team Name,Players,Total Score,Games Played,Average Score,Created Date');
      data.teams.forEach((team: any) => {
        const playerNames = team.player_ids.map((id: string) => {
          const player = data.players.find((p: any) => p.id === id);
          return player ? player.player_name : 'Unknown';
        }).join('; ');
        const avgScore = team.games_played > 0 ? (team.total_score / team.games_played).toFixed(2) : '0.00';
        const createdDate = new Date(team.created_date).toISOString().split('T')[0];
        lines.push(`"${team.team_name}","${playerNames}",${team.total_score},${team.games_played},${avgScore},${createdDate}`);
      });
      lines.push('');
    }
    
    // Add game sessions section
    if (data.game_sessions && data.game_sessions.length > 0) {
      lines.push('GAME SESSIONS');
      lines.push('Game Name,Date,Player/Team,Score,Type');
      data.game_sessions.forEach((session: any) => {
        const gameDate = new Date(session.game_date).toISOString().split('T')[0];
        
        // Individual player scores
        session.player_scores?.forEach((playerScore: any) => {
          lines.push(`"${session.game_name}",${gameDate},"${playerScore.player_name}",${playerScore.score},Individual`);
        });
        
        // Team scores
        session.team_scores?.forEach((teamScore: any) => {
          lines.push(`"${session.game_name}",${gameDate},"${teamScore.team_name}",${teamScore.score},Team`);
        });
      });
    }
    
    return lines.join('\n');
  };

  const handleDownloadHistory = async () => {
    if (!group) return;

    setExporting(true);
    try {
      const downloadUrl = `${EXPO_PUBLIC_BACKEND_URL}/api/groups/${id}/download-csv`;
      
      if (Platform.OS === 'web') {
        // For web platform, use direct download
        window.open(downloadUrl, '_blank');
        Alert.alert(
          'Download Started!',
          'Your board game history download has started. The CSV file should appear in your Downloads folder.'
        );
      } else {
        // For mobile platforms, use WebBrowser to open the download URL
        // The browser will handle the download automatically
        await WebBrowser.openBrowserAsync(downloadUrl, {
          presentationStyle: WebBrowser.WebBrowserPresentationStyle.FORM_SHEET,
          controlsColor: '#007AFF',
        });
        
        Alert.alert(
          'Download Started!',
          'Your board game history download has started. The CSV file should appear in your device\'s Files app or Downloads folder.'
        );
      }
    } catch (error) {
      console.error('Error downloading history:', error);
      Alert.alert('Download Failed', 'Failed to download group history. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  const handleUploadHistory = async () => {
    if (!group) return;

    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['text/csv', 'text/comma-separated-values', 'application/csv'],
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const asset = result.assets[0];
        Alert.alert(
          'Import Group History',
          `This will replace ALL current group data with the data from "${asset.name}". This action cannot be undone.\n\nAre you sure you want to continue?`,
          [
            { text: 'Cancel', style: 'cancel' },
            {
              text: 'Import',
              style: 'destructive',
              onPress: () => performImport(asset)
            }
          ]
        );
      }
    } catch (error) {
      console.error('Error picking file:', error);
      Alert.alert('Error', 'Failed to open file picker. Please try again.');
    }
  };

  const handleEditGroupName = async () => {
    if (!group) return;

    Alert.prompt(
      'Edit Group Name',
      `Current name: ${group.group_name}\n\nEnter new group name:`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Save',
          onPress: async (newName) => {
            if (!newName || newName.trim() === '') {
              Alert.alert('Error', 'Group name cannot be empty');
              return;
            }

            if (newName.trim() === group.group_name) {
              return; // No change needed
            }

            try {
              const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/groups/${group.id}/name`, {
                method: 'PUT',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  group_name: newName.trim()
                }),
              });

              if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to update group name');
              }

              // Update the group state
              setGroup(prev => prev ? { ...prev, group_name: newName.trim() } : null);

              Alert.alert('Success', 'Group name updated successfully!');
            } catch (error) {
              console.error('Error updating group name:', error);
              Alert.alert('Error', 'Failed to update group name. Please try again.');
            }
          }
        }
      ],
      'plain-text',
      group.group_name
    );
  };

  const performImport = async (asset: any) => {
    setImporting(true);
    try {
      let fileData;
      
      if (Platform.OS === 'web') {
        // For web platform, create FormData with the file
        const formData = new FormData();
        formData.append('file', asset as File);
        fileData = formData;
      } else {
        // For mobile platforms, the file is already available through DocumentPicker

        const formData = new FormData();
        formData.append('file', {
          uri: asset.uri,
          type: asset.mimeType || 'text/csv',
          name: asset.name,
        } as any);
        fileData = formData;
      }

      const uploadResponse = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/groups/${id}/import-csv`, {
        method: 'POST',
        body: fileData,
      });

      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json();
        throw new Error(errorData.detail || 'Failed to import data');
      }

      const result = await uploadResponse.json();
      
      Alert.alert(
        'Import Complete',
        `Successfully imported:\n• ${result.imported.players} players\n• ${result.imported.teams} teams\n• ${result.imported.game_sessions} game sessions`,
        [
          {
            text: 'OK',
            onPress: () => {
              // Refresh the page data
              loadGroupData();
            }
          }
        ]
      );
    } catch (error) {
      console.error('Error importing group data:', error);
      Alert.alert(
        'Import Failed', 
        `Failed to import group data: ${error.message || 'Unknown error'}\n\nPlease make sure you selected a valid group history file.`
      );
    } finally {
      setImporting(false);
    }
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
            <View style={styles.groupNameContainer}>
              <Text style={styles.groupName}>{group.group_name}</Text>
              <TouchableOpacity
                style={styles.editButton}
                onPress={() => handleEditGroupName()}
                activeOpacity={0.7}
              >
                <Ionicons name="pencil" size={16} color="#007AFF" />
              </TouchableOpacity>
            </View>
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

        {/* Data Management Buttons */}
        <View style={styles.dataManagementContainer}>
          <Text style={styles.dataManagementTitle}>Data Management</Text>
          
          <View style={styles.dataManagementButtons}>
            <TouchableOpacity
              style={[styles.dataButton, styles.downloadButton]}
              onPress={handleDownloadHistory}
              disabled={exporting}
              activeOpacity={0.8}
            >
              {exporting ? (
                <ActivityIndicator size="small" color="#007AFF" />
              ) : (
                <Ionicons name="download" size={20} color="#007AFF" />
              )}
              <Text style={styles.downloadButtonText}>
                {exporting ? 'Exporting...' : 'Download History'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.dataButton, styles.uploadButton]}
              onPress={handleUploadHistory}
              disabled={importing}
              activeOpacity={0.8}
            >
              {importing ? (
                <ActivityIndicator size="small" color="#ff6b35" />
              ) : (
                <Ionicons name="cloud-upload" size={20} color="#ff6b35" />
              )}
              <Text style={styles.uploadButtonText}>
                {importing ? 'Importing...' : 'Upload History'}
              </Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.dataManagementHint}>
            Download to backup your group data, or upload to restore from a previous backup.
          </Text>
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
  groupNameContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  groupName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  editButton: {
    padding: 6,
    borderRadius: 6,
    backgroundColor: '#f0f0f0',
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
  statChevron: {
    position: 'absolute',
    top: 8,
    right: 8,
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
  dataManagementContainer: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
    marginTop: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  dataManagementTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
    textAlign: 'center',
  },
  dataManagementButtons: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  dataButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    minHeight: 48,
    gap: 8,
  },
  downloadButton: {
    backgroundColor: '#e3f2fd',
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  uploadButton: {
    backgroundColor: '#fff3e0',
    borderWidth: 1,
    borderColor: '#ff6b35',
  },
  downloadButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },
  uploadButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ff6b35',
  },
  dataManagementHint: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    lineHeight: 16,
  },
});