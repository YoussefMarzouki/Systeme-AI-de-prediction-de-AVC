import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CaseEvaluationComponent } from './case-evaluation.component';

describe('CaseEvaluationComponent', () => {
  let component: CaseEvaluationComponent;
  let fixture: ComponentFixture<CaseEvaluationComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CaseEvaluationComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CaseEvaluationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
