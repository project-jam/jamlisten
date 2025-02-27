import { promises as fs } from "fs";
import { watch } from "fs";
import { join } from "path";
import { Logger } from "../utils/logger";

interface BlacklistEntry {
  username: string;
  reason: string;
  timestamp: number;
}

export class BlacklistManager {
  private static instance: BlacklistManager;
  private blacklistPath: string;
  private blacklistedUsers: Map<string, BlacklistEntry>;
  private fileWatcher: fs.FSWatcher | null = null;

  private constructor() {
    this.blacklistPath = join(__dirname, "..", "..", "blacklist.env");
    this.blacklistedUsers = new Map();
    this.loadBlacklist();
    this.startFileWatcher();
  }

  public static getInstance(): BlacklistManager {
    if (!BlacklistManager.instance) {
      BlacklistManager.instance = new BlacklistManager();
    }
    return BlacklistManager.instance;
  }

  private startFileWatcher(): void {
    try {
      this.fileWatcher = watch(
        this.blacklistPath,
        async (eventType, filename) => {
          if (filename) {
            await this.loadBlacklist();
          }
        },
      );
    } catch (error) {
      Logger.error("Failed to start blacklist file watcher:", error);
    }
  }

  private async loadBlacklist(): Promise<void> {
    try {
      const data = await fs.readFile(this.blacklistPath, "utf-8");
      const lines = data.split("\n").filter((line) => line.trim());

      const newBlacklist = new Map<string, BlacklistEntry>();
      lines.forEach((line) => {
        const [id, username, reason, dateString] = line
          .split("=")
          .map((part) => part.trim());

        if (id && username && reason && dateString) {
          // Convert MM/DD/YYYY/HH:mm:ss to Unix timestamp
          const [datePart, timePart] = dateString.split("/");
          const [month, day, year] = datePart.split("/");
          const timestamp = Math.floor(
            new Date(`${year}-${month}-${day}T${timePart}`).getTime() / 1000,
          );

          newBlacklist.set(id, {
            username,
            reason,
            timestamp,
          });
        }
      });

      this.blacklistedUsers = newBlacklist;
      Logger.info(`Loaded ${this.blacklistedUsers.size} blacklist entries`);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") {
        Logger.info("No blacklist file found, will create when needed");
      } else {
        Logger.error("Error loading blacklist:", error);
      }
    }
  }

  private async saveBlacklist(): Promise<void> {
    try {
      this.fileWatcher?.removeAllListeners();

      const content = Array.from(this.blacklistedUsers.entries())
        .map(([id, entry]) => {
          // Keep the original date format in the file
          const date = new Date(entry.timestamp * 1000);
          const formatted =
            date.toLocaleDateString("en-US", {
              month: "2-digit",
              day: "2-digit",
              year: "numeric",
            }) +
            "/" +
            date.toLocaleTimeString("en-US", {
              hour12: false,
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            });

          return `${id}=${entry.username}=${entry.reason}=${formatted}`;
        })
        .join("\n");

      await fs.writeFile(this.blacklistPath, content);
      this.startFileWatcher();
    } catch (error) {
      Logger.error("Error saving blacklist:", error);
      throw error;
    }
  }

  public async addUser(
    userId: string,
    username: string,
    reason: string,
  ): Promise<void> {
    try {
      const timestamp = Math.floor(Date.now() / 1000); // Store as seconds
      this.blacklistedUsers.set(userId, {
        username,
        reason,
        timestamp,
      });
      await this.saveBlacklist();
      Logger.info(`Blacklisted user with ID ${userId}`);
    } catch (error) {
      Logger.error(`Failed to blacklist user: ${userId}`, error);
      throw error;
    }
  }

  public async removeUser(userId: string): Promise<boolean> {
    try {
      const removed = this.blacklistedUsers.delete(userId);
      if (removed) {
        await this.saveBlacklist();
        Logger.info(`Removed user ${userId} from blacklist`);
      }
      return removed;
    } catch (error) {
      Logger.error(`Failed to remove user from blacklist: ${userId}`, error);
      throw error;
    }
  }

  public async changeReason(userId: string, newReason: string): Promise<void> {
    try {
      const currentEntry = this.blacklistedUsers.get(userId);
      if (!currentEntry) {
        throw new Error("User not found in blacklist");
      }

      this.blacklistedUsers.set(userId, {
        ...currentEntry,
        reason: newReason,
      });

      await this.saveBlacklist();
      Logger.info(`Updated blacklist reason for user ${userId}: ${newReason}`);
    } catch (error) {
      Logger.error(
        `Failed to update blacklist reason for user: ${userId}`,
        error,
      );
      throw error;
    }
  }

  public searchBlacklist(query: string): Array<[string, BlacklistEntry]> {
    query = query.toLowerCase();
    const results = Array.from(this.blacklistedUsers.entries()).filter(
      ([id, entry]) => {
        return (
          id.toLowerCase().includes(query) ||
          entry.username.toLowerCase().includes(query) ||
          entry.reason.toLowerCase().includes(query)
        );
      },
    );

    if (results.length > 0) {
      Logger.info(`Found ${results.length} blacklist entries matching query`);
    }

    return results;
  }

  public getBlacklistInfo(userId: string): BlacklistEntry | null {
    const info = this.blacklistedUsers.get(userId);
    if (info) {
      const date = new Date(info.timestamp).toLocaleDateString("en-US", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
      Logger.debug(
        `Retrieved blacklist info for ID ${userId} (Blacklisted on ${date})`,
      );
    }
    return info || null;
  }

  public isBlacklisted(userId: string): boolean {
    return this.blacklistedUsers.has(userId);
  }

  public cleanup(): void {
    if (this.fileWatcher) {
      this.fileWatcher.close();
      this.fileWatcher = null;
      Logger.debug("Blacklist file watcher closed");
    }
  }
}
