from airflow.sdk.exceptions import AirflowFailException
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator


class TriggerUnpausedDagRunOperator(TriggerDagRunOperator):
    """TriggerDagRunOperator that fails at once if the DAG to trigger is paused.

    A run triggered on a paused DAG stays queued until the DAG is unpaused, and with
    wait_for_completion=True the triggering task waits on it with no timeout: on the dev instance,
    where tests_all was paused, the nightly orchestrator runs hung from 6 to 9 Nov 2026.

    Stand-in for `fail_when_dag_is_paused=True`, which the standard provider doesn't support on
    Airflow 3 yet (it raises NotImplementedError). Not needed once the pipelines no longer trigger
    other DAGs (SIT-414).
    """

    def execute(self, context):
        if context["ti"].get_dag(self.trigger_dag_id).is_paused:
            raise AirflowFailException(
                f"DAG {self.trigger_dag_id!r} is paused: a run triggered on it would never start. "
                "Unpause it (or don't run this step) and retry."
            )
        return super().execute(context)
