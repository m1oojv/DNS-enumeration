import shutil

import luigi


class TargetList(luigi.ExternalTask):
    """ External task.  `TARGET_FILE` is generated manually by the user from target's scope. """

    target_file = luigi.Parameter()

    def output(self):
        """ Returns the target output for this task. target_file.domains

        In this case, it expects a domain named passed as TARGET env variable.
        target identifier.  The returned target output will be target_file.domains.

        Example:  Given a TARGET_FILE of tesla where the first line is tesla.com; tesla.domains
        is written to disk.

        Returns:
            luigi.local_target.LocalTarget
        """

        f = open(f"{self.target_file}", "w")
        f.write(self.target_file)
        f.close()

        shutil.copy(f"{self.target_file}", f"{self.target_file}.domains")
        return luigi.LocalTarget(f"{self.target_file}.domains")
