# Dex Scheduler Investigation Archive

Archived and organized 2026-09-21. These are retained engineering evidence, not
current setup instructions. The game went through several failed scheduler
designs before the accepted implementation; preserving the negative controls
and build identities makes future work, including the Stats redesign, auditable.

Words such as "current", "next", "proposed", "no fix installed" and "passed" inside
a report apply to its own build and stage of investigation. Numeric breakpoints,
resource bills and local artifact paths can be obsolete. Follow the maintained
[implementation](../../pokedex_animation_scheduler.md),
[validation guide](../../dex_scheduler_validation.md),
[host tools](../../dex_timing_model.md) and
[live backlog](../../pokedex_selected_bug_backlog.md) for present behavior.

## Measurement And Calibration

| Report | Why retained |
| --- | --- |
| [Scheduler investigation](dex_scheduler_investigation.md) | Overall failure chains, capture identities and original decision gates |
| [Boundary timing](dex_timing_boundary_investigation.md) | IRQ, HALT, DMA and PPU corrections; residuals versus exact-state comparisons |
| [Dusknoir/Bastiodon capture procedure](dex_timing_capture_dusknoir_bastiodon.md) | Historical capture contract and addresses |
| [Five-species capture procedure](dex_timing_capture_five_species.md) | Broader historical capture contract and addresses |
| [Full-sequence replay](dex_full_replay_results.md) | Main/hold/idle continuation and independent-core comparison |
| [End-to-end captures](dex_end_to_end_capture_results.md) | Actual Weavile/Dusknoir start-to-finish evidence |
| [Host-model development history](dex_timing_model_history.md) | Original guide with detailed component measurements and calibration chronology |

## Policy And Implementation Experiments

| Report | Why retained |
| --- | --- |
| [Scheduler policy experiments](dex_scheduler_policy_experiments.md) | Candidate work release and failed controls |
| [Publication budget](dex_publication_budget_results.md) | Physical-VBlank bounds, OAM and publication-window controls |
| [Steady-display recovery](dex_steady_publication_results.md) | Quiet ownership and remaining Garchomp counterexample |
| [Garchomp finishing](dex_garchomp_finishing_results.md) | Complete-chain finishing admission and actual starting-state expansion |
| [Queue construction](dex_queue_construction_results.md) | Measured queue-copy savings and negative controls |
| [Headroom and synthesized cries](dex_headroom_synth_results.md) | Reserve comparison, fixed tile-copy costs and synth validation |
| [Implementation preflight](dex_scheduler_implementation_preflight.md) | Planned resource/calling contracts before integration |

## Regression And Checkpoint History

| Report | Why retained |
| --- | --- |
| [Groudon decode targets](dex_groudon_target_results.md) | Expanded-test misses and lookahead diagnosis |
| [Target regression](dex_target_regression_results.md) | Eighteen-species/phase matrix, unused-tail controls and compiled correction |
| [Validation history](dex_scheduler_validation_history.md) | Older ROM identities, integration measurements and checkpoint progression |
| [Backlog investigation history](dex_backlog_investigation_history.md) | Detailed animation/cry progression and explicitly superseded Description-page hypothesis |
| [Test-save, Unown and Seviper history](dex_seviper_new_entry_testing.md) | Backup provenance, valid Unown form correction and completed finite-script retest |

The current [all-species cold results](../../dex_cold_listing_results.md) stay
outside the archive because they are the latest accepted instrumented-build
evidence. The [New Dex Entry procedure](../../dex_new_entry_testing.md) is also
maintained separately: that owner audit is still pending.

## Preservation Rules

- Keep these curated Markdown records in Git; do not ignore the archive with generated build output.
- Preserve measured values, ROM/core hashes, failed controls and uncertainty qualifications. Fix navigation or add context without silently revising an old result into a new claim.
- Local `build/` scripts, reports, frozen ROMs and save-state exports are not portable repo inputs. Reproduction requires the exact artifacts named by each report.
- No old breakpoint or test-encounter recipe is automatically valid in a new link.
- A successful host policy prototype is not an installed game fix. A later current-link pass does not retroactively calibrate incomplete old captures.
