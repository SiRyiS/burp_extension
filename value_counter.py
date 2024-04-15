from burp import IBurpExtender, IContextMenuFactory, ITab, IHttpListener, IExtensionStateListener
from javax.swing import JMenuItem, JPanel, JScrollPane, JTextArea, JOptionPane
import re
import json

# class
class BurpExtender(IBurpExtender, IContextMenuFactory, ITab, IHttpListener, IExtensionStateListener):

    # method call for extensions
    def registerExtenderCallbacks(self, callbacks):
        self.callbacks = callbacks
        self.helpers = callbacks.helpers
        self.context = None

        # name of the extension
        callbacks.setExtensionName("Value Counter")

        callbacks.registerContextMenuFactory(self)
        callbacks.registerHttpListener(self)
        callbacks.registerExtensionStateListener(self)

        # extension tab
        self.panel = JPanel()
        self.text_area = JTextArea()
        self.scroll_pane = JScrollPane(self.text_area)
        self.panel.add(self.scroll_pane)

        # UI component
        callbacks.customizeUiComponent(self.panel)

        # add extension tab
        callbacks.addSuiteTab(self)

    # get the tab caption
    def getTabCaption(self):
        return "Value Counter"

    # get component of the tab
    def getUiComponent(self):
        return self.panel

    # create context menu items
    def createMenuItems(self, invocation):
        self.context = invocation
        menu_items = []
        menu_items.append(JMenuItem("Count Values", actionPerformed=self.count_values))
        return menu_items

    # count values
    def count_values(self, event):
        selected_message = self.context.getSelectedMessages()[0]
        response = selected_message.getResponse()

        if response:
            # extraction
            headers, body = self.helpers.bytesToString(response).split('\r\n\r\n', 1)

            # ask for field to search for
            search_field = JOptionPane.showInputDialog(None, "Enter the field to search for (e.g., 'username' or 'id'):")

            if search_field:
                values = set()

                try:
                    # added JSON parsing for more accurate count
                    json_body = json.loads(body)

                    # recursivly find values of the specified field
                    def find_values(obj, field):
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                if key == field:
                                    values.add(str(value))
                                elif isinstance(value, (dict, list)):
                                    find_values(value, field)
                        elif isinstance(obj, list):
                            for item in obj:
                                find_values(item, field)

                    find_values(json_body, search_field)

                except json.JSONDecodeError:
                    # not a valid JSON, fall back to regex
                    pattern = re.compile(r'"{}":"([^"]+)"'.format(re.escape(search_field)))
                    # search within the body and exclude the header
                    matches = pattern.findall(body)
                    values.update(matches)
                
                count = len(values)

                self.text_area.setText("Unique {} Count: {}".format(search_field, count))
