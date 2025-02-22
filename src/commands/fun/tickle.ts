import {
  ChatInputCommandInteraction,
  SlashCommandBuilder,
  EmbedBuilder,
} from "discord.js";
import type { Command } from "../../types/Command";
import { Logger } from "../../utils/logger";
import { getGif, getRandomMessage } from "../../utils/otakuGifs";

// Playful decorative elements
const tickleDecorations = [
  "✨",
  "💫",
  "🌟",
  "⭐",
  "😆",
  "🤣",
  "😹",
  "💝",
  "🎈",
  "🎪",
  "🎭",
  "🎪",
  "🎡",
  "🎨",
  "🌈",
  "🦋",
  "🎀",
  "🎵",
  "🎶",
  "💫",
];

// Laughing kaomoji
const tickleKaomoji = [
  "(っ˘ω˘ς)",
  "(๑˃ᴗ˂)ﻭ",
  "(｡♥‿♥｡)",
  "(ﾉ´ヮ`)ﾉ*: ･ﾟ",
  "(*≧▽≦)",
  "(●´∀｀●)",
  "(｡◕‿◕｡)",
  "(✿◠‿◠)",
  "(*´▽`*)",
  "(◍•ᴗ•◍)",
  "(ノ^ω^)ノ",
  "ヽ(>∀<☆)ノ",
];

// Enhanced tickle messages with more chaos
const tickleMessages = [
  (user: string, target: string) =>
    `aww, **${user}** gives **${target}** a tick- WHAT IS HAPPENING?!`,
  (user: string, target: string) =>
    `**${user}** unleashes TICKLE CHAOS on **${target}**! RUN!!!`,
  (user: string, target: string) =>
    `**${user}** initiates tickle warfare with **${target}**! RESISTANCE IS FUTILE!`,
  (user: string, target: string) =>
    `**${user}** tickles **${target}** and- OH NO THE TICKLE MONSTER IS LOOSE!`,
  (user: string, target: string) =>
    `ALERT! **${user}** has begun Operation: Tickle **${target}**!`,
  (user: string, target: string) =>
    `**${user}** activates their special move: ULTIMATE TICKLE on **${target}**!`,
  (user: string, target: string) =>
    `**${user}** starts a tickle revolution with **${target}**! MADNESS ENSUES!`,
  (user: string, target: string) =>
    `BREAKING NEWS: **${user}** causes tickle catastrophe with **${target}**!`,
  (user: string, target: string) =>
    `**${user}** and **${target}** enter the TICKLE DIMENSION! NO ESCAPE!`,
  (user: string, target: string) =>
    `**${user}** unleashes forbidden tickle techniques on **${target}**!`,
];

// Helper functions for random elements
function getRandomDecorations(count: number): string {
  return Array(count)
    .fill(0)
    .map(
      () =>
        tickleDecorations[Math.floor(Math.random() * tickleDecorations.length)],
    )
    .join(" ");
}

function getRandomKaomoji(): string {
  return tickleKaomoji[Math.floor(Math.random() * tickleKaomoji.length)];
}

export const command: Command = {
  data: new SlashCommandBuilder()
    .setName("tickle")
    .setDescription("Release the tickle monster! (｡◕‿◕｡)")
    .setDMPermission(true)
    .addUserOption((option) =>
      option
        .setName("user")
        .setDescription("Your tickle victim (prepare for chaos!)")
        .setRequired(true),
    ),

  async execute(interaction: ChatInputCommandInteraction) {
    await interaction.deferReply();

    try {
      const target = interaction.options.getUser("user");

      // Don't allow tickling yourself
      if (target?.id === interaction.user.id) {
        await interaction.editReply({
          embeds: [
            new EmbedBuilder()
              .setColor("#ff3838")
              .setDescription(
                `❌ Self-tickling creates a paradox! Don't break the universe! ${getRandomKaomoji()}`,
              )
              .setFooter({
                text: "Find someone else to tickle into oblivion! 😆",
              }),
          ],
        });
        return;
      }

      const [gifUrl, message] = await Promise.all([
        getGif("tickle"),
        Promise.resolve(
          getRandomMessage(
            tickleMessages,
            interaction.user.toString(),
            target.toString(),
          ),
        ),
      ]);

      // Create decorative borders
      const topDecorations = getRandomDecorations(3);
      const bottomDecorations = getRandomDecorations(3);

      const embed = new EmbedBuilder()
        .setColor("#ffd1dc") // Light pink for chaotic tickles!
        .setTitle(`${topDecorations} TICKLE CHAOS ACTIVATED! ${topDecorations}`)
        .setDescription(
          `${message} ${getRandomKaomoji()}\n\n${bottomDecorations}`,
        )
        .setImage(gifUrl)
        .setFooter({
          text: `The tickle monster strikes again! ${getRandomKaomoji()}`,
          iconURL: interaction.user.displayAvatarURL(),
        })
        .setTimestamp();

      await interaction.editReply({ embeds: [embed] });
    } catch (error) {
      Logger.error("Tickle command failed:", error);
      await interaction.editReply({
        embeds: [
          new EmbedBuilder()
            .setColor("#ff3838")
            .setDescription(
              `❌ The tickle monster got distracted by a butterfly! Try again! ${getRandomKaomoji()}`,
            ),
        ],
      });
    }
  },
};
