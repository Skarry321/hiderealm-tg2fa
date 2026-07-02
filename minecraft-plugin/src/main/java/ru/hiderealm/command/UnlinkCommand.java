package ru.hiderealm.command;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.entity.Player;
import ru.hiderealm.HideRealmPlugin;

public class UnlinkCommand implements org.bukkit.command.CommandExecutor {

    private static final Component PREFIX = Component.text()
            .append(Component.text("HideRealm ", NamedTextColor.GOLD))
            .append(Component.text(">> ", NamedTextColor.GRAY))
            .build();

    public UnlinkCommand(HideRealmPlugin plugin) {
    }

    @Override
    public boolean onCommand(org.bukkit.command.CommandSender sender, org.bukkit.command.Command command, String label, String[] args) {
        if (!(sender instanceof Player player)) {
            sender.sendMessage(Component.text("Only players can use this command."));
            return true;
        }

        player.sendMessage(PREFIX.append(
                Component.text("Используйте /unlink в Telegram боте для отвязки аккаунта.", NamedTextColor.WHITE)));
        return true;
    }
}
