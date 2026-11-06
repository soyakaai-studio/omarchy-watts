import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

BarWidget {
  id: root
  moduleName: "soyaka.watts"

  property var watts: null
  property string source: "cpu"
  property int limit: 100
  // The charge limit shows only for a moment after you change it, as confirmation.
  property bool limitFlash: false
  property bool limitSeen: false
  onLimitChanged: {
    if (!limitSeen) { limitSeen = true; return }
    limitFlash = true
    limitFlashTimer.restart()
  }
  Timer { id: limitFlashTimer; interval: 2000; onTriggered: root.limitFlash = false }
  property bool failed: false
  property string tip: ""
  readonly property string script: Qt.resolvedUrl("watts.py").toString().replace("file://", "")

  function refresh() {
    run([])
  }

  property var pending: null

  function run(args) {
    // A key press during a poll runs right after it instead of being dropped.
    if (proc.running) {
      if (args.length) pending = args
      return
    }
    proc.command = ["python3", "-I", root.script].concat(args)
    proc.running = true
  }

  // Popup with the same details as the tooltip, so keyboard bar navigation can open it.
  // Shape contract for shell.summon/hide/toggle: open/close/opened on the widget root.
  property bool isOpen: false
  readonly property bool opened: isOpen
  property bool popoutSwitchClosing: false

  function open() {
    isOpen = true
    root.refresh()
  }

  function close() {
    isOpen = false
  }

  function closeForPopoutSwitch() {
    popoutSwitchClosing = true
    close()
    Qt.callLater(function() { popoutSwitchClosing = false })
  }

  KeyboardPanel {
    id: panel
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.isOpen
    focusTarget: keys
    contentWidth: panel.fittedContentWidth(Style.space(380))
    contentHeight: panel.fittedContentHeight(body.implicitHeight)

    PanelKeyCatcher {
      id: keys
      anchors.fill: parent
      onCloseRequested: root.close()
      // Return flips the charge limit, same as clicking the widget.
      onReturnRequested: root.run(["toggle"])
      onTabRequested: function(direction) { if (root.bar) root.bar.switchPanelFrom(root, direction) }

      Text {
        id: body
        width: parent.width
        text: root.tip
        color: Color.foreground
        font.family: root.bar ? root.bar.fontFamily : Style.font.family
        font.pixelSize: Style.font.body
        lineHeight: 1.25
        wrapMode: Text.Wrap
      }
    }
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  Process {
    id: proc
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          const d = JSON.parse(text)
          root.watts = d.watts
          root.source = d.source
          root.limit = d.limit
          root.failed = d.error
          root.tip = d.tip
        } catch (e) {}
        if (root.pending) {
          const next = root.pending
          root.pending = null
          Qt.callLater(function() { root.run(next) })
        }
      }
    }
  }

  Timer {
    interval: 3000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: root.run([])
  }

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    // Battery icon = whole-laptop draw; chip icon = CPU only (on AC). The limit flashes briefly after a change.
    property string icon: root.source === "battery" ? "󱐋" : "󰻠"
    property string value: (root.watts === null ? "–" : root.watts) + "W"
      + (root.limitFlash ? " ·" + root.limit : "")
    text: icon + " " + value
    // Icon and value drawn apart with a 3 px gap.
    fontSize: Style.font.bodySmall
    labelVisible: false
    fixedWidth: vertical ? -1 : split.implicitWidth + scaledHorizontalMargin * 2
    Row {
      id: split
      anchors.centerIn: parent
      spacing: 3
      Repeater {
        model: [button.icon, button.value]
        Text {
          required property string modelData
          anchors.verticalCenter: parent.verticalCenter
          text: modelData
          color: button.foreground
          font.family: button.fontFamily
          font.pixelSize: button.fontSize
          renderType: Text.NativeRendering
        }
      }
    }
    foreground: root.failed ? Color.urgent : (root.bar ? root.bar.barForeground : Color.foreground)
    tooltipText: root.isOpen ? "" : root.tip
    onPressed: root.run(["toggle"])
  }
}
