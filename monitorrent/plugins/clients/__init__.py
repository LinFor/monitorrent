from monitorrent.plugins.trackers import Topic


class TopicSettings(object):
    download_dir = None

    def __init__(self, download_dir, download_category):
        """
        :type download_dir: str | None
        """
        super(TopicSettings, self).__init__()
        self.download_dir = download_dir
        self.download_category = download_category

    @staticmethod
    def from_topic(topic):
        """
        :type topic: Topic
        """
        return TopicSettings(topic.download_dir, topic.download_category)
