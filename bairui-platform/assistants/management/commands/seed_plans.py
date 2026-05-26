from django.core.management.base import BaseCommand

from assistants.models import Plan


class Command(BaseCommand):
    help = "Seed default commercial plans."

    def handle(self, *args, **options):
        plans = [
            {
                "code": "starter",
                "name": "Starter",
                "description": "个人轻量助理，适合体验和低频使用。",
                "monthly_price_cents": 0,
                "assistant_limit": 1,
                "task_limit_monthly": 100,
                "storage_limit_mb": 512,
                "memory_enabled": False,
                "advanced_tools_enabled": False,
            },
            {
                "code": "pro",
                "name": "Pro",
                "description": "长期记忆与多工具能力，适合日常工作和研究。",
                "monthly_price_cents": 3900,
                "assistant_limit": 5,
                "task_limit_monthly": 1200,
                "storage_limit_mb": 5120,
                "memory_enabled": True,
                "advanced_tools_enabled": False,
            },
            {
                "code": "research",
                "name": "Research",
                "description": "研究资料库、长文档处理和高级模型额度。",
                "monthly_price_cents": 9900,
                "assistant_limit": 10,
                "task_limit_monthly": 5000,
                "storage_limit_mb": 20480,
                "memory_enabled": True,
                "advanced_tools_enabled": True,
            },
            {
                "code": "team",
                "name": "Team",
                "description": "团队共享资料、多成员和多子 Agent 编排。",
                "monthly_price_cents": 29900,
                "assistant_limit": 30,
                "task_limit_monthly": 20000,
                "storage_limit_mb": 102400,
                "memory_enabled": True,
                "advanced_tools_enabled": True,
            },
        ]
        for plan in plans:
            Plan.objects.update_or_create(code=plan["code"], defaults=plan)
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(plans)} plans."))
