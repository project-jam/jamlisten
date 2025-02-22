import {
  ChatInputCommandInteraction,
  SlashCommandBuilder,
  EmbedBuilder,
} from "discord.js";
import type { Command } from "../../types/Command";
import { Logger } from "../../utils/logger";
import { getGif, getRandomMessage } from "../../utils/otakuGifs";

// Playful decorative elements
const pokeDecorations = [
  "👉",
  "👆",
  "✨",
  "💫",
  "⭐",
  "💢",
  "💭",
  "❗",
  "❕",
  "💨",
  "🌟",
  "☆",
  "⚡",
  "💫",
  "✌️",
  "🫵",
  "🎯",
  "🎪",
  "🎭",
  "🎡",
];

// Mischievous kaomoji
const pokeKaomoji = [
  "(･ω<)☆",
  "(｀∀´)Ψ",
  "(づ｡◕‿‿◕｡)づ",
  "(｀∀´)ノ",
  "(´･ω･`)つ",
  "(｀⌒´メ)",
  "(・∀・)ノ",
  "(｀▽´)-σ",
  "(σ･∀･)σ",
  "(っ´ω`)ﾉ",
  "(^・ω・^)",
  "( ´∀｀)ノ",
];

// Enhanced poke messages with more playfulness
const pokeMessages = [
  (user: string, target: string) =>
    `**${user}** pokes **${target}** with mischievous intent!`,
  (user: string, target: string) =>
    `**${user}** just can't stop poking **${target}**! Poke poke!`,
  (user: string, target: string) =>
    `hey **${target}**! **${user}** demands attention with endless pokes!`,
  (user: string, target: string) =>
    `**${user}** unleashes a barrage of pokes on **${target}**!`,
  (user: string, target: string) =>
    `poke poke poke! **${user}** won't leave **${target}** alone!`,
  (user: string, target: string) =>
    `**${target}** becomes **${user}**'s poking target!`,
  (user: string, target: string) =>
    `**${user}** sneakily approaches **${target}** for a surprise poke!`,
  (user: string, target: string) =>
    `a wild poke appears! **${user}** strikes **${target}**!`,
  (user: string, target: string) =>
    `*poke poke poke* **${user}** launches Operation: Annoy **${target}**!`,
  (user: string, target: string) =>
    `**${user}** initiates tactical poking maneuvers on **${target}**!`,
];

// Helper functions for random elements
function getRandomDecorations(count: number): string {
  return Array(count)
    .fill(0)
    .map(
      () => pokeDecorations[Math.floor(Math.random() * pokeDecorations.length)],
    )
    .join(" ");
}

function getRandomKaomoji(): string {
  return pokeKaomoji[Math.floor(Math.random() * pokeKaomoji.length)];
}

export const command: Command = {
  data: new SlashCommandBuilder()
    .setName("poke")
    .setDescription("Initiate tactical poking! (｀∀´)ノ")
    .setDMPermission(true)
    .addUserOption((option) =>
      option
        .setName("user")
        .setDescription("Your unsuspecting poke target")
        .setRequired(true),
    ),

  async execute(interaction: ChatInputCommandInteraction) {
    await interaction.deferReply();

    try {
      const target = interaction.options.getUser("user");

      // Don't allow poking yourself
      if (target?.id === interaction.user.id) {
        await interaction.editReply({
          embeds: [
            new EmbedBuilder()
              .setColor("#ff3838")
              .setDescription(
                `❌ Poking yourself? That's not how this works! ${getRandomKaomoji()}`,
              )
              .setFooter({
                text: "Find someone else to bother! 👉",
              }),
          ],
        });
        return;
      }

      const [gifUrl, message] = await Promise.all([
        getGif("poke"),
        Promise.resolve(
          getRandomMessage(
            pokeMessages,
            interaction.user.toString(),
            target.toString(),
          ),
        ),
      ]);

      // Create decorative borders
      const topDecorations = getRandomDecorations(3);
      const bottomDecorations = getRandomDecorations(3);

      const embed = new EmbedBuilder()
        .setColor("#87CEEB") // Sky blue for playful pokes!
        .setTitle(`${topDecorations} POKE ATTACK! ${topDecorations}`)
        .setDescription(
          `${message} ${getRandomKaomoji()}\n\n${bottomDecorations}`,
        )
        .setImage(gifUrl)
        .setFooter({
          text: `Mission accomplished! Target has been poked! ${getRandomKaomoji()}`,
          iconURL: interaction.user.displayAvatarURL(),
        })
        .setTimestamp();

      await interaction.editReply({ embeds: [embed] });
    } catch (error) {
      Logger.error("Poke command failed:", error);
      await interaction.editReply({
        embeds: [
          new EmbedBuilder()
            .setColor("#ff3838")
            .setDescription(
              `❌ Critical miss! Your poke failed to connect! ${getRandomKaomoji()}`,
            ),
        ],
      });
    }
  },
};
